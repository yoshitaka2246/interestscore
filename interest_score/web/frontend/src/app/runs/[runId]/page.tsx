"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { type RunDetail, getRun, resultVideoUrl } from "@/lib/api";
import { StatusBadge } from "@/components/status-badge";

export default function RunDetailPage() {
  const params = useParams<{ runId: string }>();
  const runId = params.runId;

  const [run, setRun] = useState<RunDetail | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const fetchRun = async () => {
      const result = await getRun(runId);
      if (cancelled) return;

      if (!result.ok) {
        setErrorMessage(result.error);
        return;
      }
      setRun(result.data);
      if (result.data.status !== "running") {
        clearInterval(interval);
      }
    };

    const interval = setInterval(fetchRun, 3000);
    fetchRun();

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [runId]);

  return (
    <main className="mx-auto max-w-3xl w-full flex-1 px-6 py-10 space-y-8">
      <Link href="/" className="text-sm text-neutral-500 hover:underline">
        ← 一覧に戻る
      </Link>

      <header className="flex items-center gap-3">
        <h1 className="font-mono text-xl font-semibold">{runId}</h1>
        {run && <StatusBadge status={run.status} />}
      </header>

      {errorMessage && (
        <p className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">{errorMessage}</p>
      )}

      {run?.status === "running" && (
        <p className="text-sm text-neutral-500">処理中です…(自動更新)</p>
      )}

      {run?.error && (
        <pre className="whitespace-pre-wrap rounded-md bg-red-50 p-4 text-xs text-red-700">
          {run.error}
        </pre>
      )}

      {run?.hasVideo && (
        <section>
          <video controls className="w-full rounded-lg border border-neutral-200">
            <source src={resultVideoUrl(runId)} type="video/mp4" />
          </video>
        </section>
      )}

      {run && run.metadata && (
        <section className="rounded-lg border border-neutral-200 bg-white p-6 text-sm">
          <dl className="grid grid-cols-2 gap-2">
            {Object.entries(run.metadata).map(([key, value]) => (
              <div key={key} className="contents">
                <dt className="text-neutral-500">{key}</dt>
                <dd className="font-mono break-all">{String(value)}</dd>
              </div>
            ))}
          </dl>
        </section>
      )}

      {run && run.persons.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-lg font-medium">人物別 Interest Score</h2>
          <div className="overflow-x-auto rounded-lg border border-neutral-200 bg-white">
            <table className="w-full text-sm">
              <thead className="bg-neutral-50 text-left text-xs text-neutral-500">
                <tr>
                  <th className="px-4 py-2">Track ID</th>
                  <th className="px-4 py-2">滞在時間(秒)</th>
                  <th className="px-4 py-2">歩行速度(px/秒)</th>
                  <th className="px-4 py-2">Interest Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {run.persons.map((person) => (
                  <tr key={person.trackId}>
                    <td className="px-4 py-2 font-mono">{person.trackId}</td>
                    <td className="px-4 py-2">
                      {(person.endTimeSec - person.startTimeSec).toFixed(2)}
                    </td>
                    <td className="px-4 py-2">{person.speedRaw.toFixed(1)}</td>
                    <td className="px-4 py-2 font-semibold">{person.interestScore.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </main>
  );
}
