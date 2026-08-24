from __future__ import annotations

from dataclasses import dataclass

from backend.app.config import Settings


@dataclass(frozen=True)
class SampleFile:
    name: str
    media_type: str
    content: str


def build_sample_files(settings: Settings) -> tuple[SampleFile, ...]:
    runtime = settings.cloud_runtime_evidence
    if runtime:
        service, revision = runtime
        deployment = f"""# Deployment evidence

Status: runtime-verified
Platform: Google Cloud Run
Service: {service}
Revision: {revision}
Project: {settings.google_cloud_project or "injected-by-cloud-run"}
Region: {settings.tasks_location}
Persistent state: Firestore collection closeout_runs
Background dispatch: Cloud Tasks queue {settings.tasks_queue}
"""
    else:
        deployment = """# Deployment evidence

Status: pending
Platform: local development runtime
Cloud Run service: unavailable
Cloud Run revision: unavailable
Persistent state: in-memory development repository
Background dispatch: in-process development dispatcher
"""

    return (
        SampleFile(
            name="README.md",
            media_type="text/markdown",
            content="""# Closeout

An autonomous operations agent built with Gemini 3.5 Flash, Google ADK,
Cloud Run, Firestore, and Cloud Tasks.

## Run locally

Install dependencies and start the API. See deployment.md for Cloud Run.

## Demo

The agent ingests a delivery workspace, verifies requirements, and produces a
closeout packet with an evidence ledger.
""",
        ),
        SampleFile(
            name="requirements.md",
            media_type="text/markdown",
            content="""# Submission requirements

- Select the Taskmaster category.
- Include an English project description.
- Link a reproducible code repository.
- Include a clear architecture diagram.
- Provide a public demo video under four minutes with Cloud Run proof.
- Explain Gemini 3.5, Google ADK, and Google Cloud usage.
""",
        ),
        SampleFile(
            name="deployment.md",
            media_type="text/markdown",
            content=deployment,
        ),
        SampleFile(
            name="architecture.mmd",
            media_type="text/plain",
            content="""flowchart LR
  UI[Web workspace] --> API[Cloud Run API]
  API --> TASKS[Cloud Tasks]
  TASKS --> ADK[Google ADK workflow]
  ADK --> GEMINI[Gemini 3.5 Flash]
  API --> DB[(Firestore)]
""",
        ),
        SampleFile(
            name="demo-notes.txt",
            media_type="text/plain",
            content="""00:00 problem and value proposition
00:28 start live closeout run
01:30 inspect requirement evidence
02:20 show autonomous repairs and bundle
03:05 show Cloud Run, Firestore, and logs
03:38 architecture and closing
""",
        ),
    )
