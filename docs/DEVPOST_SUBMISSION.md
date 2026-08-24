# Devpost submission copy

Replace only the bracketed external URLs after they have been opened and checked.

## Project name

Closeout

## Tagline

The autonomous last-mile agent that turns fragmented project evidence into a
verified, reproducible closeout bundle.

## Track

Taskmaster

## Inspiration

The hardest part of a high-stakes project is often not creating the work. It is
closing the last mile: requirements are spread across documents, evidence lives
in logs and repositories, external gates are easy to overclaim, and the final
package is assembled manually under deadline pressure. Static checklists can
describe this problem, but they cannot finish the work or prove what happened.

We built Closeout to act like a rigorous release operator: autonomous where the
action is bounded and reversible, and deliberately honest where proof depends on
an external system or a human owner.

## What it does

Closeout ingests a small text workspace and runs an event-driven, five-stage
workflow in the background: Intake, Map, Verify, Close, and Seal. It inventories
artifacts, maps obligations to evidence, uses Gemini to propose a structured plan,
executes only policy-approved tools, repairs reversible gaps, and preserves real
external blockers. It then produces a requirement-to-evidence ledger and a
reproducible ZIP with SHA-256 hashes for every payload artifact.

The operator console makes autonomy inspectable. Every stage, actor, action,
evidence source, confidence score, and blocker is visible. A generated video
script does not become proof of a public video, and a local build does not become
proof of Cloud Run. Closeout is designed to close work without erasing the
difference between an artifact and an externally verified fact.

## How we built it

The public application is a React and TypeScript console served by a FastAPI
service on Cloud Run. Firestore stores durable run state and private inputs in
separate collections. Cloud Tasks dispatches authenticated, at-least-once jobs to
a private Cloud Run worker.

The worker uses Google Agent Development Kit 2 with Gemini 3.5 Flash. Gemini must
return a Pydantic-validated plan whose actions come from a closed literal set.
Every effect then passes through the same deterministic tool-registry gate. The
workflow is idempotent: completed runs are no-ops, active leases suppress
duplicates, and failed or stale runs rebuild derived state from persisted inputs.

The final bundle uses stable ZIP metadata and a manifest with SHA-256 hashes. The
same workflow also runs locally with in-memory adapters and a clearly labeled
deterministic demo mode.

## Challenges we ran into

The central challenge was making autonomy useful without making evidence loose.
An LLM can propose a convincing closeout narrative, but it must not decide that
an external gate is complete. We separated planning from execution, constrained
the model output schema, centralized the action allowlist, and made deterministic
validators the authority for every verdict.

At-least-once background delivery also forced us to design retry behavior before
deployment. Inputs are persisted separately, leases are explicit, exceptions are
saved and re-raised, and bundle generation is byte-reproducible.

## Accomplishments that we're proud of

- One action starts a real multistep background workflow.
- Uploaded content is never executed and is bounded by type, count, and size.
- Model proposals cannot escape the action registry.
- Every requirement links to inspectable evidence and an explicit verdict.
- Reversible gaps are repaired while external blockers remain visible.
- Identical inputs produce identical audited bundle bytes.
- The complete operator journey is tested on desktop and mobile.

## What we learned

Trustworthy agents need two different kinds of intelligence: a model that can
interpret messy intent, and a deterministic control plane that can prove which
effects were allowed and which evidence actually exists. Agentic UX also needs to
show the work at the right level: enough detail to audit a decision without
forcing the operator to read raw logs.

## What's next for Closeout

Next we would add organization-specific requirement packs, signed attestations,
retention policies, Cloud Armor or authenticated workspaces, repository and CI
connectors, and human approval nodes for irreversible actions. The same closeout
loop can serve compliance packets, procurement responses, releases, research
artifacts, and regulated handoffs.

## Built with

Google ADK, Gemini 3.5 Flash, Vertex AI, Cloud Run, Cloud Tasks, Firestore,
FastAPI, Pydantic, React, TypeScript, Vite, Playwright, Docker, and Python.

## Links

- Try it: `[PENDING_CLOUD_RUN_URL]`
- Source: `[PENDING_GITHUB_URL]`
- Demo video: `[PENDING_PUBLIC_VIDEO_URL]`
- Architecture diagram: `frontend/public/closeout-system.png`
