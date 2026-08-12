import { z } from "zod";

const instanceStateSchema = z.enum(["running", "stopped", "pending", "stopping", "unknown"]);
export type InstanceState = z.infer<typeof instanceStateSchema>;

const stateResponseSchema = z.object({ state: instanceStateSchema });
const errorResponseSchema = z.object({ error: z.string() });

export type InstanceApiResult =
  | { ok: true; state: InstanceState }
  | { ok: false; error: string };

async function handleResponse(res: Response): Promise<InstanceApiResult> {
  const json: unknown = await res.json();

  if (!res.ok) {
    const parsed = errorResponseSchema.safeParse(json);
    return { ok: false, error: parsed.success ? parsed.data.error : `HTTP ${res.status}` };
  }

  const parsed = stateResponseSchema.safeParse(json);
  if (!parsed.success) {
    return { ok: false, error: "レスポンス形式が不正です" };
  }
  return { ok: true, state: parsed.data.state };
}

export async function getInstanceState(): Promise<InstanceApiResult> {
  try {
    const res = await fetch("/api/instance");
    return await handleResponse(res);
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

export async function setInstanceState(
  action: "start" | "stop",
  password: string
): Promise<InstanceApiResult> {
  try {
    const res = await fetch("/api/instance", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, password }),
    });
    return await handleResponse(res);
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}
