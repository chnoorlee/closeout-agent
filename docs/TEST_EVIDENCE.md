# Verification evidence

Verified locally on Windows and against the live Google Cloud deployment on
2026-08-25.

| Gate | Command | Result |
| --- | --- | --- |
| Python lint | `uv run ruff check backend` | Pass |
| Python types | `uv run mypy backend/app` | Pass |
| Dependency consistency | `uv pip check` and `npm audit --omit=dev` | Pass, 0 incompatible packages and 0 vulnerabilities |
| Backend behavior | `uv run pytest -W error --cov=backend.app --cov-report=term-missing` | 14 passed, 86% line coverage, no warnings |
| TypeScript | `npm run typecheck` | Pass |
| Component tests | `npm test` | 1 passed |
| Production build | `npm run build` | Pass |
| Browser journeys | `npm run e2e` | 2 passed, desktop and mobile |
| PowerShell parser | Parses `scripts/deploy.ps1` without errors | Pass |
| OCI image build | Locked `uv sync --locked --no-dev --no-editable` build | Pass, 112,511,301 bytes |
| Container identity | `docker exec closeout-final-verification id` | Pass, non-root UID/GID 100/101 |
| Container workflow | Health, run, metrics, ZIP, and manifest hash smoke | Pass, 8/8 manifest entries accounted for |
| Container browser journeys | `$env:E2E_BASE_URL='http://127.0.0.1:8083'; npm run e2e` | 2 passed, desktop and mobile |
| Static asset containment | Traversal probes using raw and percent-encoded parent segments | Pass, all rejected with HTTP 404 while `/` remained HTTP 200 |
| Recording truth gate | Run recorder against deterministic local runtime | Pass, refused recording until `live-gemini` is reported |
| Public health | `GET /api/health` on Cloud Run | Pass, `live-gemini`, Firestore, Google Cloud Tasks |
| Cloud identity boundary | Public internal-task POST and anonymous worker POST | Pass, HTTP 405 and HTTP 403 respectively |
| Public browser journeys | `$env:E2E_BASE_URL='https://closeout-7ejjj4sb5a-uc.a.run.app'; npm run e2e` | 2 passed, desktop and mobile |
| Live agent workflow | Uploaded three real text artifacts | Pass, run `99dd0f732e31`, 88% coverage, Gemini/ADK event persisted |
| Task delivery | Cloud Run worker request log | Pass, HTTP 202 in 8.67 seconds on revision `closeout-worker-00003-2px` |
| Live bundle | Download and independently hash ZIP plus manifest entries | Pass, bundle `c82c0886...` matched and 5/5 listed entries matched |
| Live demo capture | `npm run record:demo` against the public URL | Pass, 81.68 seconds, 1280 x 720, raw SHA-256 `de5b852e...` |
| Narrated demo media | `.\scripts\build-demo-media.ps1` | Pass, 81.68 seconds, VP8 + Opus, 5,059,817 bytes, SHA-256 `4f7a487a...` |
| Public CI | GitHub Actions `verify` for commit [`e3919b0`](https://github.com/chnoorlee/closeout-agent/commit/e3919b024b4ffecb2de73ba3354f59836b350031) | [Pass](https://github.com/chnoorlee/closeout-agent/actions/runs/32797802193), backend, frontend, and 2 browser journeys |

The browser journey uploads three text artifacts, completes the five-stage
workflow, verifies the 75% evidence score, one autonomous repair, two preserved
external blockers, and a downloadable ZIP. The mobile assertion uses a 390 x 844
viewport and preserves all requirement, evidence, confidence, and verdict data.
The desktop journey also returns to a fresh upload workspace, reopens the sealed
run from history, and uses the Bundles navigation to reach the download control.
The container workflow independently recomputed the downloaded bundle SHA-256,
then checked the byte length and SHA-256 of every file listed in `MANIFEST.json`.
The final image was also probed with `curl --path-as-is` to ensure SPA fallback
resolution cannot escape the built frontend directory. The final live bundle
contained six ZIP members: five evidence files listed in `MANIFEST.json` plus
the manifest itself. The live demo was decoded in Chromium at seven points from
the opening title through the sealed bundle and passed nonblank-frame checks.
The continuous capture visibly identifies the public `.run.app` origin and the
Cloud Run, Cloud Tasks, private-worker, Firestore, Vertex AI, and Gemini path.
The narrated media decoded all 2,042 video frames and the complete audio stream.
Chromium reported one video track, one audio track, `readyState=4`, and no media
error during unmuted playback. The narration measured -21.0 dB mean and -2.8 dB
peak volume. Its copied VP8 packet hash exactly matched the raw live capture, so
adding the Opus narration did not replace or re-encode the visual evidence.

## Evidence boundary

- **Verified:** deterministic local workflow, upload constraints, action
  allowlist, atomic processing leases, structured AI schema boundary, retries,
  stable ZIPs, responsive UI, public/private Cloud Run topology, Gemini 3.5 Flash
  through Google ADK, Cloud Tasks dispatch, Firestore persistence, and public CI.
- **Pending external proof:** public hosting for the locally verified demo video,
  social post, and Devpost submission receipt.
