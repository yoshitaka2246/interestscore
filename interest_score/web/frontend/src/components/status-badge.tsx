import type { RunStatus } from "@/lib/api";

const STYLES: Record<RunStatus, string> = {
  running: "bg-amber-100 text-amber-800",
  done: "bg-emerald-100 text-emerald-800",
  failed: "bg-red-100 text-red-800",
};

const LABELS: Record<RunStatus, string> = {
  running: "実行中",
  done: "完了",
  failed: "失敗",
};

export function StatusBadge({ status }: { status: RunStatus }) {
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${STYLES[status]}`}>
      {LABELS[status]}
    </span>
  );
}
