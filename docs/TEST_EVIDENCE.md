# Verification evidence

Verified locally on Windows on 2026-08-25. These gates establish source and
container behavior; they do not establish a live Google Cloud deployment.

| Gate | Command | Result |
| --- | --- | --- |
| Python lint | `uv run ruff check backend` | Pass |
| Python types | `uv run mypy backend/app` | Pass |
| Dependency consistency | `uv pip check` and `npm audit --omit=dev` | Pass, 0 incompatible packages and 0 vulnerabilities |
| Backend behavior | `uv run pytest -W error --cov=backend.app --cov-report=term-missing` | 11 passed, 83% line coverage, no warnings |
| TypeScript | `npm run typecheck` | Pass |
| Component tests | `npm test` | 1 passed |
| Production build | `npm run build` | Pass |
| Browser journeys | `npm run e2e` | 2 passed, desktop and mobile |
| PowerShell parser | Parses `scripts/deploy.ps1` without errors | Pass |
| OCI image build | Locked `uv sync --locked --no-dev --no-editable` build | Pass, 112,516,748 bytes |
| Container identity | `docker exec closeout-verification id` | Pass, non-root UID/GID 100/101 |
| Container workflow | Health, run, metrics, ZIP, and manifest hash smoke | Pass, 8/8 manifest entries accounted for |
| Container browser journeys | `E2E_BASE_URL=http://127.0.0.1:8082 npm run e2e` | 2 passed, desktop and mobile |

The browser journey uploads three text artifacts, completes the five-stage
workflow, verifies the 75% evidence score, one autonomous repair, two preserved
external blockers, and a downloadable ZIP. The mobile assertion uses a 390 x 844
viewport and preserves all requirement, evidence, confidence, and verdict data.
The container workflow independently recomputed the downloaded bundle SHA-256,
then checked the byte length and SHA-256 of every file listed in `MANIFEST.json`.

## Evidence boundary

- **Verified:** deterministic local workflow, upload constraints, action
allowlist, atomic processing leases, structured AI schema boundary, retries,
stable ZIPs, responsive UI.
- **Implemented but not live-verified:** ADK/Gemini call, Firestore repository,
  Cloud Tasks dispatcher, Cloud Run topology, and IAM bootstrap.
- **Pending external proof:** hosted Cloud Run URL, live Gemini event, public
  repository URL, public demo video, social post, and Devpost submission receipt.
