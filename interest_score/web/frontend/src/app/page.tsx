"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  type ConfigInfo,
  type RunSummary,
  type VideoInfo,
  listConfigs,
  listRuns,
  listVideos,
  startRun,
  uploadVideo,
} from "@/lib/api";
import { StatusBadge } from "@/components/status-badge";

export default function HomePage() {
  const [videos, setVideos] = useState<VideoInfo[]>([]);
  const [configs, setConfigs] = useState<ConfigInfo[]>([]);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<string>("");
  const [selectedConfig, setSelectedConfig] = useState<string>("");
  const [isUploading, setIsUploading] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const [videosResult, configsResult, runsResult] = await Promise.all([
      listVideos(),
      listConfigs(),
      listRuns(),
    ]);

    if (videosResult.ok) {
      setVideos(videosResult.data);
      setSelectedVideo((current) => current || videosResult.data[0]?.name || "");
    } else {
      setErrorMessage(videosResult.error);
    }

    if (configsResult.ok) {
      setConfigs(configsResult.data);
      setSelectedConfig((current) => current || configsResult.data[0]?.name || "");
    } else {
      setErrorMessage(configsResult.error);
    }

    if (runsResult.ok) {
      setRuns(runsResult.data);
    } else {
      setErrorMessage(runsResult.error);
    }
  }, []);

  useEffect(() => {
    // refresh()内のsetStateはPromise.all解決後(非同期)に実行されるため実質問題ないが、
    // react-hooks/set-state-in-effectのヒューリスティックには引っかかるため個別に抑制する
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, [refresh]);

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setErrorMessage(null);
    const result = await uploadVideo(file);
    setIsUploading(false);

    if (!result.ok) {
      setErrorMessage(result.error);
      return;
    }
    setSelectedVideo(result.data.name);
    await refresh();
  };

  const handleStartRun = async () => {
    if (!selectedVideo || !selectedConfig) return;

    setIsStarting(true);
    setErrorMessage(null);
    const result = await startRun(selectedVideo, selectedConfig);
    setIsStarting(false);

    if (!result.ok) {
      setErrorMessage(result.error);
      return;
    }
    await refresh();
  };

  return (
    <main className="mx-auto max-w-3xl w-full flex-1 px-6 py-10 space-y-8">
      <header>
        <h1 className="text-2xl font-semibold">Interest Score</h1>
        <p className="text-sm text-neutral-600">
          店頭広告に対する通行人関心度推定システム
        </p>
      </header>

      {errorMessage && (
        <p className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
          {errorMessage}
        </p>
      )}

      <section className="rounded-lg border border-neutral-200 bg-white p-6 space-y-4">
        <h2 className="text-lg font-medium">動画をアップロード</h2>
        <input
          type="file"
          accept="video/mp4,video/quicktime,video/x-msvideo"
          onChange={handleUpload}
          disabled={isUploading}
          className="block w-full text-sm"
        />
        {isUploading && <p className="text-sm text-neutral-500">アップロード中…</p>}
      </section>

      <section className="rounded-lg border border-neutral-200 bg-white p-6 space-y-4">
        <h2 className="text-lg font-medium">パイプラインを実行</h2>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <label className="text-sm">
            動画
            <select
              value={selectedVideo}
              onChange={(e) => setSelectedVideo(e.target.value)}
              className="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2"
            >
              {videos.map((video) => (
                <option key={video.name} value={video.name}>
                  {video.name}
                </option>
              ))}
            </select>
          </label>

          <label className="text-sm">
            Config
            <select
              value={selectedConfig}
              onChange={(e) => setSelectedConfig(e.target.value)}
              className="mt-1 block w-full rounded-md border border-neutral-300 px-3 py-2"
            >
              {configs.map((config) => (
                <option key={config.name} value={config.name} disabled={!config.valid}>
                  {config.name}
                  {!config.valid ? "(無効)" : ""}
                </option>
              ))}
            </select>
          </label>
        </div>

        <button
          type="button"
          onClick={handleStartRun}
          disabled={isStarting || !selectedVideo || !selectedConfig}
          className="rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
        >
          {isStarting ? "実行を開始中…" : "実行する"}
        </button>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">実行履歴</h2>
        {runs.length === 0 ? (
          <p className="text-sm text-neutral-500">まだ実行結果がありません。</p>
        ) : (
          <ul className="divide-y divide-neutral-200 rounded-lg border border-neutral-200 bg-white">
            {runs.map((run) => (
              <li key={run.runId}>
                <Link
                  href={`/runs/${run.runId}`}
                  className="flex items-center justify-between px-4 py-3 hover:bg-neutral-50"
                >
                  <div>
                    <p className="font-mono text-sm">{run.runId}</p>
                    <p className="text-xs text-neutral-500">
                      {run.inputVideo ?? "-"}
                      {run.numTracks !== null ? ` ・ ${run.numTracks}人検出` : ""}
                    </p>
                  </div>
                  <StatusBadge status={run.status} />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
