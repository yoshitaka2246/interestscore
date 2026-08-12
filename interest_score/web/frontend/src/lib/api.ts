import { z } from "zod";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const videoInfoSchema = z.object({
  name: z.string(),
  sizeBytes: z.number(),
});

const configInfoSchema = z.object({
  name: z.string(),
  valid: z.boolean(),
});

const personScoreSchema = z.object({
  trackId: z.number(),
  startTimeSec: z.number(),
  endTimeSec: z.number(),
  dwellTimeRaw: z.number(),
  speedRaw: z.number(),
  interestScore: z.number(),
});

const runStatusSchema = z.enum(["running", "done", "failed"]);

const runSummarySchema = z.object({
  runId: z.string(),
  status: runStatusSchema,
  inputVideo: z.string().nullable(),
  numTracks: z.number().nullable(),
  numFrames: z.number().nullable(),
  createdAt: z.string().nullable(),
});

const runDetailSchema = z.object({
  runId: z.string(),
  status: runStatusSchema,
  metadata: z.record(z.string(), z.unknown()).nullable(),
  persons: z.array(personScoreSchema),
  hasVideo: z.boolean(),
  error: z.string().nullable(),
});

export type VideoInfo = z.infer<typeof videoInfoSchema>;
export type ConfigInfo = z.infer<typeof configInfoSchema>;
export type PersonScore = z.infer<typeof personScoreSchema>;
export type RunStatus = z.infer<typeof runStatusSchema>;
export type RunSummary = z.infer<typeof runSummarySchema>;
export type RunDetail = z.infer<typeof runDetailSchema>;

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };

// backendはsnake_caseで返すため、フロント(camelCase)用に変換する
function toCamel(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(toCamel);
  }
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([key, v]) => [
        key.replace(/_([a-z0-9])/g, (_, c: string) => c.toUpperCase()),
        toCamel(v),
      ])
    );
  }
  return value;
}

async function request<T>(
  path: string,
  schema: z.ZodType<T>,
  init?: RequestInit
): Promise<ApiResult<T>> {
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, init);
    if (!res.ok) {
      const body = await res.text();
      return { ok: false, error: `${res.status}: ${body}` };
    }
    const json = await res.json();
    const parsed = schema.safeParse(toCamel(json));
    if (!parsed.success) {
      return { ok: false, error: `レスポンス形式が不正です: ${parsed.error.message}` };
    }
    return { ok: true, data: parsed.data };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { ok: false, error: `APIに接続できません: ${message}` };
  }
}

export function listVideos(): Promise<ApiResult<VideoInfo[]>> {
  return request("/api/videos", z.array(videoInfoSchema));
}

export async function uploadVideo(file: File): Promise<ApiResult<VideoInfo>> {
  const formData = new FormData();
  formData.append("file", file);
  return request("/api/videos", videoInfoSchema, {
    method: "POST",
    body: formData,
  });
}

export function listConfigs(): Promise<ApiResult<ConfigInfo[]>> {
  return request("/api/configs", z.array(configInfoSchema));
}

export function listRuns(): Promise<ApiResult<RunSummary[]>> {
  return request("/api/runs", z.array(runSummarySchema));
}

export function getRun(runId: string): Promise<ApiResult<RunDetail>> {
  return request(`/api/runs/${encodeURIComponent(runId)}`, runDetailSchema);
}

export function startRun(
  videoName: string,
  configName: string
): Promise<ApiResult<RunSummary>> {
  return request("/api/runs", runSummarySchema, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ video_name: videoName, config_name: configName }),
  });
}

export function resultVideoUrl(runId: string): string {
  return `${API_BASE_URL}/static/results/${encodeURIComponent(runId)}/result.mp4`;
}
