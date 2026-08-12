import * as fs from "fs";
import * as path from "path";

import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as iam from "aws-cdk-lib/aws-iam";
import * as route53 from "aws-cdk-lib/aws-route53";
import { Construct } from "constructs";

export interface BackendStackProps extends cdk.StackProps {
  envName: "dev" | "prod";
  domainName: string;
  subdomain: string;
  vercelOrigin: string;
  computeType: "cpu" | "gpu";
}

// "cpu"は安価な検証用、"gpu"はYOLO推論を高速化したい時に切り替える(-c computeType=gpu)。
// g4dn.2xlarge: NVIDIA T4(16GB) + 8vCPU/32GB。動画デコード等の前処理がCPUボトルネックに
// ならないよう、GPUはxlargeと同じT4のままCPU/メモリを増やした構成を選んでいる。
const INSTANCE_TYPE_BY_COMPUTE: Record<"cpu" | "gpu", ec2.InstanceType> = {
  cpu: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.LARGE),
  gpu: ec2.InstanceType.of(ec2.InstanceClass.G4DN, ec2.InstanceSize.XLARGE2),
};

// AWS Deep Learning Base AMI(NVIDIA driver同梱、Ubuntu 26.04)。ap-northeast-1限定でAMI IDを
// 直接指定している(SSM Latest パラメータがこのAMI系列には無いため)。更新する場合は
// `aws ec2 describe-images --owners amazon --filters "Name=name,Values=Deep Learning Base*Ubuntu*"`
// で最新IDを確認する。
const GPU_AMI_ID_AP_NORTHEAST_1 = "ami-0afd7aa8518a6f0a1";

export class BackendStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: BackendStackProps) {
    super(scope, id, props);

    cdk.Tags.of(this).add("Project", "interest-score");
    cdk.Tags.of(this).add("Env", props.envName);
    cdk.Tags.of(this).add("Stack", this.stackName);
    cdk.Tags.of(this).add("ManagedBy", "cdk");

    const fqdn = `${props.subdomain}.${props.domainName}`;

    // NAT Gatewayはコストが高く単一パブリックインスタンス構成には不要なため作らない
    const vpc = new ec2.Vpc(this, "Vpc", {
      vpcName: `interest-score-vpc-${props.envName}`,
      maxAzs: 1,
      natGateways: 0,
      subnetConfiguration: [{ name: "Public", subnetType: ec2.SubnetType.PUBLIC, cidrMask: 24 }],
    });

    // SSH(22番ポート)は開けず、Session Manager経由でアクセスする
    const securityGroup = new ec2.SecurityGroup(this, "BackendSecurityGroup", {
      vpc,
      securityGroupName: `interest-score-backend-sg-${props.envName}`,
      description: "Interest Score backend: HTTPS + ACME challenge only, no SSH",
      allowAllOutbound: true,
    });
    securityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(443), "HTTPS");
    securityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(80), "HTTP (ACME challenge / redirect)");

    const role = new iam.Role(this, "InstanceRole", {
      roleName: `interest-score-backend-role-${props.envName}`,
      assumedBy: new iam.ServicePrincipal("ec2.amazonaws.com"),
      managedPolicies: [iam.ManagedPolicy.fromAwsManagedPolicyName("AmazonSSMManagedInstanceCore")],
    });

    const userDataTemplate = fs.readFileSync(
      path.join(__dirname, "../scripts/user-data.sh.template"),
      "utf-8"
    );
    const userDataScript = userDataTemplate
      .replaceAll("__CORS_ORIGINS__", `${props.vercelOrigin},https://${fqdn}`)
      .replaceAll("__DOMAIN__", fqdn);

    // CPU: Ubuntu 24.04(Python 3.12標準、CaddyのAPTリポジトリが使える)。
    // GPU: NVIDIA driver同梱のDeep Learning Base AMI(Ubuntuベースなので同じUserDataが動く)。
    const machineImage =
      props.computeType === "gpu"
        ? ec2.MachineImage.genericLinux({ "ap-northeast-1": GPU_AMI_ID_AP_NORTHEAST_1 })
        : ec2.MachineImage.fromSsmParameter(
            "/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id",
            { os: ec2.OperatingSystemType.LINUX }
          );

    const instance = new ec2.Instance(this, "BackendInstance", {
      instanceName: `interest-score-backend-${props.envName}`,
      vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
      instanceType: INSTANCE_TYPE_BY_COMPUTE[props.computeType],
      machineImage,
      securityGroup,
      role,
      userData: ec2.UserData.custom(userDataScript),
      blockDevices: [
        {
          deviceName: "/dev/sda1",
          // GPU AMI(Deep Learning Base)のスナップショットは75GB以上を要求する
          volume: ec2.BlockDeviceVolume.ebs(props.computeType === "gpu" ? 80 : 30, {
            volumeType: ec2.EbsDeviceVolumeType.GP3,
          }),
        },
      ],
    });

    // 起動/停止してもIPが変わらないようにする(証明書・DNSを壊さないため)
    const eip = new ec2.CfnEIP(this, "BackendEip", {
      domain: "vpc",
      instanceId: instance.instanceId,
    });

    const zone = route53.HostedZone.fromLookup(this, "Zone", { domainName: props.domainName });
    new route53.ARecord(this, "BackendARecord", {
      zone,
      recordName: props.subdomain,
      target: route53.RecordTarget.fromIpAddresses(eip.ref),
      ttl: cdk.Duration.minutes(5),
    });

    new cdk.CfnOutput(this, "BackendUrl", { value: `https://${fqdn}` });
    new cdk.CfnOutput(this, "InstanceId", { value: instance.instanceId });
    new cdk.CfnOutput(this, "ElasticIp", { value: eip.ref });

    // Vercel(Next.jsのAPI route)からEC2の起動/停止を操作するための最小権限ユーザー。
    // EC2はStart/Stopできるが、それ以外(TerminateInstances等)は一切許可しない。
    const instanceControlUser = new iam.User(this, "InstanceControlUser", {
      userName: `interest-score-instance-control-${props.envName}`,
    });
    instanceControlUser.addToPolicy(
      new iam.PolicyStatement({
        actions: ["ec2:StartInstances", "ec2:StopInstances"],
        resources: [
          `arn:aws:ec2:${this.region}:${this.account}:instance/${instance.instanceId}`,
        ],
      })
    );
    instanceControlUser.addToPolicy(
      // DescribeInstances(状態確認)はリソースレベル権限に対応していないため"*"が必須
      new iam.PolicyStatement({
        actions: ["ec2:DescribeInstances"],
        resources: ["*"],
      })
    );
    const instanceControlAccessKey = new iam.CfnAccessKey(this, "InstanceControlAccessKey", {
      userName: instanceControlUser.userName,
    });

    new cdk.CfnOutput(this, "InstanceControlAccessKeyId", {
      value: instanceControlAccessKey.ref,
    });
    new cdk.CfnOutput(this, "InstanceControlSecretAccessKey", {
      value: instanceControlAccessKey.attrSecretAccessKey,
    });
  }
}
