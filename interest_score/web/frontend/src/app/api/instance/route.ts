import {
  DescribeInstancesCommand,
  EC2Client,
  StartInstancesCommand,
  StopInstancesCommand,
} from "@aws-sdk/client-ec2";
import { NextResponse } from "next/server";
import { z } from "zod";

// EC2は停止中はFastAPIバックエンドが応答できないため、起動/停止はこのVercel側の
// API route(常時稼働)からAWS EC2 APIを直接叩く。IAMは対象インスタンスのStart/Stopのみ許可
// (interest_score/infra/lib/backend-stack.ts の InstanceControlUser 参照)。
export const dynamic = "force-dynamic";

const region = process.env.AWS_REGION ?? "ap-northeast-1";
const instanceId = process.env.EC2_INSTANCE_ID;

const actionRequestSchema = z.object({
  action: z.enum(["start", "stop"]),
  password: z.string(),
});

async function describeState(): Promise<string> {
  if (!instanceId) {
    throw new Error("EC2_INSTANCE_IDが設定されていません");
  }
  const client = new EC2Client({ region });
  const result = await client.send(new DescribeInstancesCommand({ InstanceIds: [instanceId] }));
  return result.Reservations?.[0]?.Instances?.[0]?.State?.Name ?? "unknown";
}

export async function GET(): Promise<NextResponse> {
  try {
    const state = await describeState();
    return NextResponse.json({ state });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

export async function POST(request: Request): Promise<NextResponse> {
  const expectedPassword = process.env.INSTANCE_CONTROL_PASSWORD;
  if (!expectedPassword) {
    return NextResponse.json(
      { error: "サーバー側でINSTANCE_CONTROL_PASSWORDが設定されていません" },
      { status: 500 }
    );
  }
  if (!instanceId) {
    return NextResponse.json({ error: "EC2_INSTANCE_IDが設定されていません" }, { status: 500 });
  }

  const body: unknown = await request.json();
  const parsed = actionRequestSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: "リクエストの形式が不正です" }, { status: 400 });
  }

  if (parsed.data.password !== expectedPassword) {
    return NextResponse.json({ error: "パスワードが違います" }, { status: 401 });
  }

  try {
    const client = new EC2Client({ region });
    if (parsed.data.action === "start") {
      await client.send(new StartInstancesCommand({ InstanceIds: [instanceId] }));
    } else {
      await client.send(new StopInstancesCommand({ InstanceIds: [instanceId] }));
    }
    const state = await describeState();
    return NextResponse.json({ state });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
