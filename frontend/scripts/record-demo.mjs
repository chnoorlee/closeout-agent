import { mkdir, rename } from "node:fs/promises";
import { dirname, resolve } from "node:path";

import { chromium } from "@playwright/test";

const baseUrl = process.env.DEMO_BASE_URL;
const outputPath = resolve(
  process.cwd(),
  process.env.DEMO_OUTPUT ?? "../artifacts/demo/closeout-demo.webm",
);
const allowDemo = process.env.DEMO_ALLOW_LOCAL === "true";

if (!baseUrl) {
  throw new Error("Set DEMO_BASE_URL to the verified public Closeout URL.");
}

const healthResponse = await fetch(new URL("/api/health", baseUrl));
if (!healthResponse.ok) {
  throw new Error(`Health check failed with HTTP ${healthResponse.status}.`);
}
const health = await healthResponse.json();
if (!allowDemo && health.ai_mode !== "live-gemini") {
  throw new Error(
    `Recording refused: expected live-gemini, received ${health.ai_mode}. ` +
      "Use DEMO_ALLOW_LOCAL=true only for a clearly labeled rehearsal.",
  );
}

await mkdir(dirname(outputPath), { recursive: true });
const browser = await chromium.launch({ channel: "chrome" });
const context = await browser.newContext({
  viewport: { width: 1280, height: 720 },
  recordVideo: { dir: dirname(outputPath), size: { width: 1280, height: 720 } },
});
const page = await context.newPage();

async function caption(kicker, title, detail, duration = 4500) {
  await page.evaluate(
    ({ kickerText, titleText, detailText }) => {
      document.querySelector("#demo-caption")?.remove();
      const overlay = document.createElement("section");
      overlay.id = "demo-caption";
      overlay.setAttribute("aria-hidden", "true");
      overlay.innerHTML = `
        <span>${kickerText}</span>
        <strong>${titleText}</strong>
        <p>${detailText}</p>
      `;
      Object.assign(overlay.style, {
        position: "fixed",
        zIndex: "9999",
        left: "28px",
        bottom: "26px",
        width: "min(560px, calc(100vw - 56px))",
        padding: "17px 20px",
        border: "1px solid #343a3f",
        borderRadius: "6px",
        background: "rgba(25, 28, 31, 0.96)",
        boxShadow: "0 14px 40px rgba(0, 0, 0, 0.25)",
        color: "#f7f8f5",
        fontFamily: '"Segoe UI", Arial, sans-serif',
        pointerEvents: "none",
      });
      const kickerNode = overlay.querySelector("span");
      const titleNode = overlay.querySelector("strong");
      const detailNode = overlay.querySelector("p");
      Object.assign(kickerNode.style, {
        display: "block",
        color: "#71d1a9",
        fontSize: "11px",
        fontWeight: "700",
        textTransform: "uppercase",
      });
      Object.assign(titleNode.style, {
        display: "block",
        marginTop: "6px",
        fontSize: "21px",
        lineHeight: "1.2",
      });
      Object.assign(detailNode.style, {
        margin: "7px 0 0",
        color: "#cbd0d3",
        fontSize: "13px",
        lineHeight: "1.45",
      });
      document.body.append(overlay);
    },
    { kickerText: kicker, titleText: title, detailText: detail },
  );
  await page.waitForTimeout(duration);
  await page.locator("#demo-caption").evaluate((element) => element.remove());
  await page.waitForTimeout(450);
}

try {
  await page.goto(baseUrl, { waitUntil: "networkidle" });
  await page.getByText("Runtime connected").waitFor();
  await page.getByRole("button", { name: "Run workspace" }).click();
  await page.getByRole("heading", { name: "Run briefing" }).waitFor();

  await caption(
    "Taskmaster track",
    "Closeout",
    "An autonomous last-mile agent for high-stakes deliverables.",
    5000,
  );
  await caption(
    "Inspect before acting",
    "One workflow, five controlled stages",
    "Closeout maps obligations to evidence, performs bounded repairs, and preserves external blockers.",
    6500,
  );

  await page.locator('input[type="file"]').setInputFiles([
    {
      name: "README.md",
      mimeType: "text/markdown",
      buffer: Buffer.from("# Closeout\n\n## Run locally\nuv run uvicorn backend.app.main:app"),
    },
    {
      name: "requirements.md",
      mimeType: "text/markdown",
      buffer: Buffer.from("# Requirements\n\nTrack: Taskmaster"),
    },
    {
      name: "architecture.mmd",
      mimeType: "text/plain",
      buffer: Buffer.from("flowchart LR\nUI --> API\nAPI --> WORKER"),
    },
  ]);
  await page.getByText("3 selected", { exact: true }).waitFor();
  await caption(
    "Real intake",
    "A workspace enters as bounded data",
    "File types, count, size, encoding, and paths are validated before the agent starts.",
    5500,
  );

  await page.getByRole("button", { name: "Start closeout" }).click();
  await caption(
    "Autonomous execution",
    "Map, verify, close, seal",
    "Gemini proposes a structured plan. Every effect still passes a deterministic tool allowlist.",
    7500,
  );
  await page.getByText("Sealed and reproducible").waitFor({ timeout: 120_000 });

  await caption(
    "Honest completion",
    "75% evidence coverage",
    "Five requirements are verified, one reversible gap is repaired, and two external gates remain blocked.",
    7000,
  );
  await page.getByRole("button", { name: "Requirements" }).click();
  await caption(
    "Evidence ledger",
    "Every verdict has a source and confidence",
    "Closeout never promotes a generated script or local build into external proof.",
    7000,
  );
  await page.getByRole("button", { name: "Activity" }).click();
  await caption(
    "Inspectable autonomy",
    "The audit trace names every stage, actor, and action",
    "Retries are safe: completed runs are no-ops and active leases suppress duplicates.",
    7000,
  );

  await page.getByRole("link", { name: "Download bundle" }).scrollIntoViewIfNeeded();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("link", { name: "Download bundle" }).click();
  await downloadPromise;
  await caption(
    "Reproducible output",
    "The result is sealed, hashed, and portable",
    "A stable ZIP contains the evidence ledger, audit events, artifacts, and a SHA-256 manifest.",
    7000,
  );
  await caption(
    "Closeout",
    "Autonomous where actions are bounded. Honest where proof is external.",
    "Built with Google ADK, Gemini 3.5 Flash, Cloud Run, Cloud Tasks, and Firestore.",
    6500,
  );
} finally {
  const video = page.video();
  await context.close();
  if (video) {
    await rename(await video.path(), outputPath);
  }
  await browser.close();
}

console.log(`Demo video written to ${outputPath}`);
