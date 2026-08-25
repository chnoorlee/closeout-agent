import { expect, test } from "@playwright/test";

test("completes and downloads an evidence-backed closeout", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 960 });
  await page.goto("/");

  await expect(page.getByText("Runtime connected")).toBeVisible();
  const health = await page.request.get("/api/health");
  expect(health.ok()).toBeTruthy();
  const isLive = (await health.json()).ai_mode === "live-gemini";
  const screenshotRoot = isLive ? "../docs/images" : "../artifacts/playwright";
  const upload = page.locator('input[type="file"]');
  if (!(await upload.isVisible())) {
    await page.getByRole("button", { name: "Run workspace" }).click();
  }
  await expect(upload).toBeAttached();
  await page.screenshot({
    path: `${screenshotRoot}/closeout-preflight-desktop.png`,
    fullPage: true,
  });

  await upload.setInputFiles([
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
  await expect(page.getByText("3 selected", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Start closeout" }).click();
  await expect(page.getByText("Sealed and reproducible")).toBeVisible({ timeout: 120_000 });
  await expect(
    page.getByLabel("Run metrics").getByText(isLive ? "88%" : "75%", { exact: true }),
  ).toBeVisible();
  await expect(page.getByText("8 obligations", { exact: true })).toBeVisible();
  await expect(
    page.getByText(
      isLive ? "1 gap repaired, 1 external gate remains" : "1 gap repaired, 2 external gates remain",
      { exact: true },
    ),
  ).toBeVisible();

  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("link", { name: "Download bundle" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/^closeout-[a-f0-9]+\.zip$/);

  await page.screenshot({
    path: `${screenshotRoot}/closeout-complete-desktop.png`,
    fullPage: true,
  });

  await page.getByRole("button", { name: "Run workspace" }).click();
  await expect(page.getByRole("heading", { name: "Run briefing" })).toBeVisible();
  await expect(page.locator('input[type="file"]')).toBeAttached();
  await page.locator(".history-item").first().click();
  await expect(page.getByText("Sealed and reproducible")).toBeVisible();
  await page.getByRole("button", { name: "Bundles" }).click();
  await expect(page.getByRole("link", { name: "Download bundle" })).toBeInViewport();
});

test("keeps the completed workspace coherent on mobile", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");

  await expect(page.getByText("Runtime connected")).toBeVisible();
  const health = await page.request.get("/api/health");
  expect(health.ok()).toBeTruthy();
  const isLive = (await health.json()).ai_mode === "live-gemini";
  const start = page.getByRole("button", { name: "Start closeout" });
  if (await start.isEnabled()) {
    await start.click();
    await expect(page.getByText("Sealed and reproducible")).toBeVisible({ timeout: 120_000 });
  }
  await expect(page.getByRole("link", { name: "Download bundle" })).toBeVisible();

  await page.screenshot({
    path: isLive
      ? "../docs/images/closeout-complete-mobile.png"
      : "../artifacts/playwright/closeout-complete-mobile.png",
    fullPage: true,
  });
});
