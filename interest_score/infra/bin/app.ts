#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";

import { BackendStack } from "../lib/backend-stack";

const app = new cdk.App();

const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION ?? "ap-northeast-1",
};

// Vercelフロントエンドの本番URL(CORS許可用)。
// cdk deploy -c vercelOrigin=https://xxx.vercel.app で上書きする。
const vercelOrigin = app.node.tryGetContext("vercelOrigin") as string | undefined;
if (!vercelOrigin) {
  throw new Error(
    "コンテキスト vercelOrigin が未設定です。例: cdk deploy -c vercelOrigin=https://interestscore.vercel.app"
  );
}

// バックエンドを公開するドメイン。Route53にホストゾーンが存在すること。
const domainName = (app.node.tryGetContext("domainName") as string | undefined) ?? "yoshi-yamamoto.com";
const subdomain = (app.node.tryGetContext("subdomain") as string | undefined) ?? "api";

// "cpu" | "gpu" — 最初はcpu。将来GPUへ移行する際は -c computeType=gpu で再デプロイする。
const computeType = ((app.node.tryGetContext("computeType") as string | undefined) ?? "cpu") as "cpu" | "gpu";

new BackendStack(app, "InterestScoreBackendStack", {
  env,
  envName: "dev",
  domainName,
  subdomain,
  vercelOrigin,
  computeType,
});
