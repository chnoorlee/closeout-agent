import type { Health, Run } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<Health>("/api/health"),
  runs: () => request<Run[]>("/api/runs"),
  run: (id: string) => request<Run>(`/api/runs/${id}`),
  startDemo: () =>
    request<Run>("/api/runs/demo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario: "hackathon-closeout" }),
    }),
  startWorkspace: (files: File[]) => {
    const body = new FormData();
    body.set("name", "Uploaded workspace");
    files.forEach((file) => body.append("files", file));
    return request<Run>("/api/runs", { method: "POST", body });
  },
  bundleUrl: (id: string) => `/api/runs/${id}/bundle`,
};
