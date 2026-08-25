# Security model

## Input boundary

- The upload endpoint accepts at most 8 UTF-8 text files, 128 KiB per file and
  384 KiB total.
- Allowed extensions are CSV, JSON, Markdown, Mermaid, SVG, TXT, YAML, and YML.
- Path components, duplicate names, NUL bytes, unsupported types, and invalid
  UTF-8 are rejected.
- Uploaded artifacts are treated as data. Closeout never executes uploaded code
  or user-supplied shell commands.
- SPA asset paths are resolved against the built frontend root. Parent-path
  traversal is rejected with HTTP 404 before any file is served.

## Model boundary

- Gemini emits structured output validated by Pydantic.
- Proposed action names are a closed `Literal` set.
- Every effect must pass the central tool-registry allowlist.
- Deterministic validators, not the model, decide completion evidence.
- External claims such as a live deployment or public video require matching
  externally verifiable evidence and cannot be repaired by prose generation.

## Cloud boundary

- The API service is public; the worker requires authenticated Cloud Tasks OIDC.
- The internal task execution route is not registered in the public service's
  Cloud Tasks dispatcher mode.
- Separate build, runtime, and task service accounts limit IAM scope. The build
  identity has `roles/run.builder`; the deployment does not add a build role to
  the default compute identity.
- Firestore stores run state separately from private input artifacts.
- Firestore delete protection is enabled by the deployment script.
- Secrets are supplied through runtime credentials or environment configuration
  and are excluded from the repository and generated bundle.

## Known production boundary

The hackathon demo is intentionally anonymous and therefore susceptible to
public traffic. Upload limits constrain cost and memory exposure, but a durable
public deployment should add Cloud Armor or an identity layer, per-principal
quotas, retention policies, and abuse monitoring before accepting sensitive or
untrusted workloads.
