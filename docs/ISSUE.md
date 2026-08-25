# Build Closeout for All Things Agentic Hackathon

## Problem

High-stakes deliverables often stall in the last mile. Requirements live in one
document, evidence in another, verification commands in a repository, and the
final package is assembled manually under deadline pressure. A checklist can
describe the work, but it does not complete it or prove that it was completed.

## Goal

Build and deploy an autonomous Taskmaster agent that turns a mixed project
workspace into a submission-ready, evidence-backed closeout bundle.

## Scope

- Ingest a seeded demo workspace and user-provided text artifacts.
- Use Gemini 3.5+ through Google ADK for requirement and evidence synthesis.
- Run deterministic, policy-scoped verification and repair tools.
- Persist resumable workflow state in Firestore when configured.
- Dispatch durable background work with Cloud Tasks when configured.
- Expose a production-quality English web workspace on Cloud Run.
- Generate a downloadable evidence ledger and closeout bundle.
- Provide tests, architecture documentation, deployment instructions, and
  Devpost-ready submission assets.

## Non-Goals

- Executing arbitrary uploaded code or shell commands.
- Claiming external links, cloud resources, or third-party approvals were
  verified when only local evidence exists.
- Automatically publishing social posts, videos, or the final Devpost entry
  without the account owner's review.

## Acceptance Criteria

- [x] A user can start the seeded closeout run in one action and watch all five
      workflow stages complete without further input.
- [x] The live path uses `gemini-3.5-flash` or newer and Google ADK; the UI and
      API clearly distinguish live AI from deterministic demo mode.
- [x] Every autonomous action is selected from an allowlisted tool registry,
      emits an audit event, and is safe to retry with the same idempotency key.
- [x] A completed run exposes a requirement-to-evidence ledger and a downloadable
      ZIP whose manifest hashes match its contents.
- [x] Local unit, API, frontend, build, and critical browser-journey checks pass.
- [x] A Cloud Run deployment is reachable and shows persistent Google Cloud
      execution evidence suitable for the demo video.
- [x] The repository includes reproducible setup, a clear architecture
      diagram, testing instructions, licensing, and all required Devpost copy.
- [ ] The final Devpost draft has a category, hosted URL, repository URL,
      architecture diagram, English description, and public demo video under
      four minutes.

## Dependencies/Blockers

- Google Cloud authentication, a billing-enabled project, and Gemini/Vertex AI
  access are required for live deployment verification.
- GitHub and Devpost authentication are required for public publishing and final
  submission.
- The user must confirm eligibility and final legal attestations.

## Status

ready

Current progress:

Implementation, public Cloud deployment, repository publication, and the public
demo video are verified. Final Devpost submission and its acceptance receipt
remain external account gates.

## Execution Gate

allowed (the user authorized autonomous project design and implementation)
