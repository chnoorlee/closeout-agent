# Demo script (3:45 target)

## 0:00-0:25 - The last-mile problem

Show a workspace with scattered requirements and evidence. Explain that a
checklist can report gaps, but Closeout performs bounded closeout work and proves
what it did.

## 0:25-0:50 - Architecture

Show the architecture image. Identify the public Cloud Run app, Firestore,
Cloud Tasks, private worker, Google ADK, Gemini 3.5 Flash, and deterministic tool
registry. Briefly show the live Cloud Run revision and Cloud Tasks execution.

## 0:50-1:25 - Real intake

Open the hosted app. Point out the live runtime badge. Select a small README,
requirements file, and architecture file, then start Closeout with one action.

## 1:25-2:25 - Autonomous work

Follow the five stages. Show Gemini's bounded plan, audit events, allowlisted
actions, and one repaired internal gap. Emphasize that the workflow continues in
the background and is safe to retry.

## 2:25-3:05 - Honest evidence

Open the requirement ledger. Contrast verified, repaired, and blocked verdicts.
Show that Closeout preserves an external blocker rather than manufacturing proof.

## 3:05-3:35 - Reproducible result

Download the ZIP. Open the manifest and ledger, then match one artifact's SHA-256.
Show the Firestore run record and completed Cloud Task.

## 3:35-3:45 - Close

Closeout turns the fragile last mile into an autonomous, inspectable, and
reproducible workflow.

## Recording gates

- Keep the published video at or below 4:00.
- Show the hosted URL, live Gemini mode, and Google Cloud evidence on screen.
- Use a public YouTube or Vimeo link and verify it in a signed-out browser.
- Do not splice local deterministic-demo footage as if it were the cloud run.

## Reproducible app recording

After the public deployment reports `live-gemini`, generate the application
walkthrough with:

```powershell
$env:DEMO_BASE_URL = 'https://your-verified-cloud-run-url'
Set-Location frontend
npm run record:demo
```

The recorder refuses deterministic demo mode by default and writes
`artifacts/demo/closeout-demo.webm`. Add a short Cloud Console shot and narration
from the timeline above before publishing the final video.
