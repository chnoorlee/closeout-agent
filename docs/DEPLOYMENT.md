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
Firestore, and Cloud Run; creates service identities and minimum role grants;
creates the Firestore database and queue; deploys a private worker; grants only
the task identity permission to invoke it; then deploys the public app from the
same immutable image.

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

The local application and deployment script are verified. A public Cloud Run URL
is pending an authenticated, billing-enabled project and must not be represented
as complete until the live checks above pass.
