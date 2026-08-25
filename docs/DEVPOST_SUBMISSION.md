# Devpost submission copy

The external links below were opened and checked before final submission.

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

Our Bring Your Own Friction was this hackathon closeout itself. We had a live
application, cloud execution logs, a repository, submission rules, and a demo
video, but no single system could determine what was actually proven, close safe
gaps, and refuse to overclaim the remaining external steps. The twist is that
Closeout does not generate another checklist: it operates on the delivery process
and packages the proof.

We built Closeout to act like a rigorous release operator: autonomous where the
action is bounded and reversible, and deliberately honest where proof depends on
an external system or a human owner.

## What it does

One action starts Closeout's event-driven, five-stage background workflow:
Intake, Map, Verify, Close, and Seal. For bounded work, it completes the workflow
without follow-up intervention. Closeout inventories artifacts, maps obligations to
evidence, uses Gemini to propose a structured plan, executes only policy-approved
tools, repairs reversible gaps, and preserves real external blockers. It finishes
with a requirement-to-evidence ledger and a reproducible ZIP containing SHA-256
hashes for every payload artifact.

The operator console makes autonomy inspectable. Every stage, actor, action,
evidence source, confidence score, and blocker is visible. A generated video
script does not become proof of a public video, and a local build does not become
proof of Cloud Run. Closeout is designed to close work without erasing the
difference between an artifact and an externally verified fact.

## How we built it

The public application is a React and TypeScript console served by a FastAPI
service on Cloud Run. Firestore stores durable run state and private inputs in
separate collections. Cloud Tasks dispatches authenticated, at-least-once jobs to
an IAM-only private Cloud Run worker using OIDC service-account identity.

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
- A production run processed three real artifacts through all five stages,
  reached 88% evidence coverage, performed one bounded repair, preserved the
  remaining external blocker, and sealed a manifest-verified ZIP.
- The public application, private worker, Cloud Task delivery, Firestore state,
  live Gemini/ADK event, and downloadable bundle were independently verified.

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

- Try it: `https://closeout-7ejjj4sb5a-uc.a.run.app`
- Source: `https://github.com/chnoorlee/closeout-agent`
- Demo video: `https://youtu.be/E83TGwgERqE`
- Architecture diagram: `https://github.com/chnoorlee/closeout-agent/blob/main/frontend/public/closeout-system.png`

## Optional developer contributions

- Public build content: `https://youtu.be/E83TGwgERqE` (Public, not unlisted;
  its description states that it was created for entering this hackathon.)
- Social post: use the reviewed draft in `docs/PUBLIC_BUILD_POST.md` only after
  publishing it from the entrant's X, LinkedIn, Instagram, or Facebook account.

## Final account checklist

- Project name: `Closeout`
- Track/category: `Taskmaster`
- Try-it URL: `https://closeout-7ejjj4sb5a-uc.a.run.app`
- Repository URL: `https://github.com/chnoorlee/closeout-agent`
- Video URL: `https://youtu.be/E83TGwgERqE`
- Upload the architecture image from `frontend/public/closeout-system.png`.
- Add the public build-content URL above to the optional contribution field.
- Review eligibility and legal attestations as the account owner, then submit.
