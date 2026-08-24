import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import App from "./App";

afterEach(() => vi.restoreAllMocks());

test("renders the operational preflight when the API has no runs", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
    const url = String(input);
    if (url.endsWith("/api/health")) {
      return Promise.resolve(new Response(JSON.stringify({
        status: "ok",
        service: "Closeout",
        model: "gemini-3.5-flash",
        framework: "Google ADK 2",
        ai_mode: "deterministic-demo",
        store: "memory",
        dispatcher: "local-background-task",
        timestamp: new Date().toISOString(),
      })));
    }
    return Promise.resolve(new Response("[]"));
  });

  render(<App />);

  expect(await screen.findByRole("heading", { name: "Run briefing" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /start closeout/i })).toBeEnabled();
  await waitFor(() => expect(screen.getByText("Runtime connected")).toBeInTheDocument());
});
