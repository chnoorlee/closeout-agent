# Google Cloud deployment

## Prerequisites

- A billing-enabled Google Cloud project
- `gcloud` installed and authenticated
- Permission to enable APIs, create service accounts, grant project IAM, create
  Firestore, Cloud Tasks, and Cloud Run resources
- Gemini 3.5 Flash access in the selected project and region

## Deploy

```powershell
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
.\scripts\deploy.ps1 -ProjectId YOUR_PROJECT_ID -Region us-central1
```

The script enables Vertex AI, Artifact Registry, Cloud Build, Cloud Tasks,
Firestore, and Cloud Run; creates separate build, runtime, and task identities
with minimum role grants; creates the Firestore database and queue; deploys a
private worker; grants only the task identity permission to invoke it; then
deploys the public app from the same immutable image. Source builds run as
`closeout-build` with the Cloud Run Builder role instead of inheriting the
project's default compute identity for this build.

## Verify

1. Open the printed public service URL and confirm the runtime badge reports the
   cloud store, Cloud Tasks dispatcher, and live Gemini mode.
2. Upload a small workspace and start a run.
3. Confirm all five stages finish and the ledger retains real external blockers.
4. Download the ZIP and compare each manifest SHA-256 with its artifact.
5. Inspect Cloud Run request logs, Cloud Tasks execution, and Firestore run/input
   documents. Capture these views for the architecture section of the demo.

## Roll back

List revisions and route traffic to the last known-good one:

```powershell
gcloud run revisions list --service closeout --region us-central1
gcloud run services update-traffic closeout --region us-central1 --to-revisions REVISION=100
```

The worker and public service share an image. Roll both services to compatible
revisions if a schema or workflow contract changes. Firestore delete protection
means rollback does not remove run evidence.

## Current status

The production topology is live in `us-central1`:

- Public app: `https://closeout-7ejjj4sb5a-uc.a.run.app`
- Private worker: `https://closeout-worker-7ejjj4sb5a-uc.a.run.app`
- Public revision: `closeout-00003-pd6`
- Worker revision: `closeout-worker-00003-2px`
- Verified run: `99dd0f732e31`

The run completed in `live-gemini` mode through Cloud Tasks, persisted in
Firestore, produced an 88% evidence score, and sealed bundle SHA-256
`c82c08861c6a9931076865fea66bf18549d33c88fff293e0f137e98801dab6c0`.
The worker returned HTTP 202 in 8.67 seconds and rejects anonymous calls with
HTTP 403. Both services run the same immutable image digest,
`sha256:5ea97cbbfaa1d83fe28d8dd95d05a301cfdb8860cec7b6bb564474c6436afb85`.
