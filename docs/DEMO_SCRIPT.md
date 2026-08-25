# Demo script (1:22 final)

The final submission video is one continuous capture of the public Cloud Run
application. English captions are burned into the recording and an accurate
English narration follows the same live workflow.

## Timeline

### 0:00-0:18 - Friction and live cloud proof

Introduce the last-mile delivery problem and Closeout. Show the public
`.run.app` origin plus the Cloud Run, Cloud Tasks, private-worker, Firestore,
Vertex AI, Gemini 3.5 Flash, and Google ADK 2 path.

### 0:18-0:33 - Bounded intake

Show the five controlled stages and upload three bounded project artifacts. Explain
that paths, file types, sizes, and encodings are validated before agent action.

### 0:33-0:51 - Autonomous execution

Start Closeout once. Show Gemini's structured plan and explain that every side
effect remains behind a deterministic, allowlisted tool boundary.

### 0:51-1:10 - Honest evidence and auditability

Show the 88% result, requirement ledger, preserved public-video blocker, and
retry-safe audit trail. A generated script or local build never becomes external
proof.

### 1:10-1:22 - Reproducible result

Download the stable ZIP and show the evidence ledger, audit events, artifacts,
and SHA-256 manifest.

## Rebuild the final media

Record a fresh live run only after the public deployment reports `live-gemini`:

```powershell
$env:DEMO_BASE_URL = 'https://closeout-7ejjj4sb5a-uc.a.run.app'
Set-Location frontend
npm.cmd run record:demo
Set-Location ..
```

Add the versioned narration without modifying the source capture:

```powershell
.\scripts\build-demo-media.ps1
```

This generates `artifacts/demo/closeout-demo-narrated.webm`. The narration source
is `docs/demo-narration.ssml`.

## Publication gates

- Keep the published video at or below 4:00.
- Show the hosted URL, live Gemini mode, and Google Cloud evidence on screen.
- Verify both video and audio streams before upload.
- Publish on YouTube or Vimeo as **Public**, not unlisted.
- Verify playback in a signed-out browser before submitting the URL.
- Do not splice local deterministic-demo footage into the cloud run.
