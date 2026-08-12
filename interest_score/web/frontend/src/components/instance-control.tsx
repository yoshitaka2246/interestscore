"use client";

import { useCallback, useEffect, useState } from "react";

import { type InstanceState, getInstanceState, setInstanceState } from "@/lib/instance-api";

const STATE_LABELS: Record<InstanceState, string> = {
  running: "起動中",
  stopped: "停止中",
  pending: "起動処理中…",
  stopping: "停止処理中…",
  unknown: "不明",
};

const STATE_STYLES: Record<InstanceState, string> = {
  running: "bg-emerald-100 text-emerald-800",
  stopped: "bg-neutral-100 text-neutral-700",
  pending: "bg-amber-100 text-amber-800",
  stopping: "bg-amber-100 text-amber-800",
  unknown: "bg-neutral-100 text-neutral-500",
};

export function InstanceControl() {
  const [state, setState] = useState<InstanceState>("unknown");
  const [password, setPassword] = useState("");
  const [isBusy, setIsBusy] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const result = await getInstanceState();
    if (result.ok) {
      setState(result.state);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, [refresh]);

  const handleAction = async (action: "start" | "stop") => {
    if (!password) {
      setErrorMessage("パスワードを入力してください");
      return;
    }

    setIsBusy(true);
    setErrorMessage(null);
    const result = await setInstanceState(action, password);
    setIsBusy(false);

    if (!result.ok) {
      setErrorMessage(result.error);
      return;
    }
    setState(result.state);
  };

  return (
    <section className="rounded-lg border border-neutral-200 bg-white p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium">AWSインスタンス</h2>
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATE_STYLES[state]}`}>
          {STATE_LABELS[state]}
        </span>
      </div>

      {errorMessage && (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{errorMessage}</p>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="パスワード"
          className="rounded-md border border-neutral-300 px-3 py-2 text-sm"
        />
        <button
          type="button"
          onClick={() => handleAction("start")}
          disabled={isBusy || state === "running" || state === "pending"}
          className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
        >
          起動
        </button>
        <button
          type="button"
          onClick={() => handleAction("stop")}
          disabled={isBusy || state === "stopped" || state === "stopping"}
          className="rounded-md bg-neutral-700 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
        >
          停止
        </button>
      </div>
    </section>
  );
}
