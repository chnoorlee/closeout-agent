from __future__ import annotations

import asyncio
import hashlib
import io
import json
import uuid
import zipfile
from collections.abc import Sequence
from datetime import timedelta

from backend.app.agent import analyze_with_adk
from backend.app.config import Settings
from backend.app.domain import (
    Artifact,
    CloseoutRun,
    Requirement,
    RunMetrics,
    RunStatus,
    Stage,
    StageStatus,
    TimelineEvent,
    Verdict,
)
from backend.app.repository import RunRepository
from backend.app.sample_data import SampleFile, build_sample_files
from backend.app.tools import (
    ALLOWED_TOOLS,
    execute_tool,
)

STAGES = (
    ("intake", "Intake"),
    ("map", "Map"),
    ("verify", "Verify"),
    ("close", "Close"),
    ("seal", "Seal"),
)
RUN_LEASE_TIMEOUT = timedelta(minutes=6)


class CloseoutWorkflow:
    def __init__(self, repository: RunRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings

    async def create_demo_run(self, scenario: str) -> CloseoutRun:
        return await self._create_run(
            name="Closeout / Devpost submission",
            scenario=scenario,
            files=build_sample_files(self.settings),
            idempotency_prefix="demo",
        )

    async def create_workspace_run(self, name: str, files: Sequence[SampleFile]) -> CloseoutRun:
        return await self._create_run(
            name=f"{name} / Closeout",
            scenario="uploaded-workspace",
            files=files,
            idempotency_prefix="workspace",
        )

    async def _create_run(
        self,
        name: str,
        scenario: str,
        files: Sequence[SampleFile],
        idempotency_prefix: str,
    ) -> CloseoutRun:
        run_id = uuid.uuid4().hex[:12]
        run = CloseoutRun(
            id=run_id,
            name=name,
            scenario=scenario,
            model=self.settings.model,
            mode="live-gemini" if self.settings.has_live_ai_config else "deterministic-demo",
            idempotency_key=f"{idempotency_prefix}:{scenario}:{run_id}",
            stages=[Stage(id=key, label=label) for key, label in STAGES],
        )
        created = await self.repository.create(run)
        await self.repository.save_files(run_id, files)
        return created

    async def process(self, run_id: str) -> None:
        claim = await self.repository.claim(run_id, RUN_LEASE_TIMEOUT)
        if not claim:
            return
        run, previous_status = claim
        if previous_status in {RunStatus.FAILED, RunStatus.RUNNING}:
            self._reset_for_retry(run, previous_status)
            await self.repository.save(run)
        try:
            files = await self.repository.get_files(run_id)
            if not files:
                raise RuntimeError("Workspace inputs are unavailable")
            await self._intake(run, files)
            await self._map(run, files)
            await self._verify(run, files)
            await self._close(run, files)
            await self._seal(run, files)
            run.status = RunStatus.COMPLETED
            await self.repository.save(run)
        except Exception as exc:
            run.status = RunStatus.FAILED
            run.error = str(exc)
            active = next(
                (stage for stage in run.stages if stage.status == StageStatus.ACTIVE),
                None,
            )
            if active:
                active.status = StageStatus.FAILED
                active.summary = "Action failed"
            self._event(
                run,
                "system",
                "Workflow stopped",
                str(exc),
                "execution-kernel",
                StageStatus.FAILED,
            )
            await self.repository.save(run)
            raise

    async def _pause(self) -> None:
        if self.settings.stage_delay_ms:
            await asyncio.sleep(self.settings.stage_delay_ms / 1000)

    async def _begin(self, run: CloseoutRun, stage_id: str, summary: str) -> None:
        stage = self._stage(run, stage_id)
        stage.status = StageStatus.ACTIVE
        stage.summary = summary
        await self.repository.save(run)
        await self._pause()

    async def _finish(self, run: CloseoutRun, stage_id: str, summary: str) -> None:
        stage = self._stage(run, stage_id)
        stage.status = StageStatus.COMPLETED
        stage.summary = summary
        await self.repository.save(run)

    async def _intake(self, run: CloseoutRun, files: Sequence[SampleFile]) -> None:
        await self._begin(run, "intake", "Fingerprinting workspace")
        result = execute_tool("inventory_workspace", files)
        run.artifacts = [
            Artifact(
                id=f"artifact-{index}",
                name=item.name,
                media_type=item.media_type,
                size_bytes=len(item.content.encode("utf-8")),
                sha256=hashlib.sha256(item.content.encode("utf-8")).hexdigest(),
            )
            for index, item in enumerate(files, start=1)
        ]
        run.metrics.autonomous_actions += 1
        self._event(run, "intake", "Workspace fingerprinted", result.summary, "intake-agent")
        await self._finish(run, "intake", f"{len(run.artifacts)} artifacts indexed")

    async def _map(self, run: CloseoutRun, files: Sequence[SampleFile]) -> None:
        await self._begin(run, "map", "Building requirement graph")
        requirements = [
            ("track", "Taskmaster category selected", "requirements.md"),
            ("description", "English product description", "requirements.md"),
            ("repository", "Reproducible repository instructions", "requirements.md"),
            ("architecture", "Architecture diagram", "requirements.md"),
            ("video", "Public demo under four minutes", "requirements.md"),
            ("cloud", "Visible Google Cloud deployment proof", "requirements.md"),
            ("security", "Credential hygiene", "Closeout policy"),
            ("ledger", "Requirement-to-evidence ledger", "Closeout policy"),
        ]
        run.requirements = [
            Requirement(id=key, title=title, source=source) for key, title, source in requirements
        ]
        if run.mode == "live-gemini":
            payload = {
                "scenario": run.scenario,
                "artifacts": [{"name": item.name, "content": item.content} for item in files],
            }
            analysis = await analyze_with_adk(self.settings, run.id, payload)
            detail = str(analysis.get("summary", "Gemini mapped the workspace"))
            proposed = [str(action) for action in analysis.get("proposed_actions", [])]
            actor = "gemini-3.5-flash / google-adk"
        else:
            detail = f"Deterministic mapper linked {len(files)} artifacts to 8 delivery obligations"
            proposed = list(ALLOWED_TOOLS)
            actor = "deterministic-mapper"
        run.planned_actions = list(
            dict.fromkeys(
                [
                    "inventory_workspace",
                    *proposed,
                    "scan_secrets",
                    "validate_submission_shape",
                    "build_manifest",
                ]
            )
        )
        run.metrics.requirements = len(run.requirements)
        run.metrics.autonomous_actions += 1
        self._event(
            run,
            "map",
            "Requirement graph created",
            detail,
            actor,
            metadata={"planned_actions": run.planned_actions},
        )
        await self._finish(run, "map", f"{len(run.requirements)} obligations mapped")

    async def _verify(self, run: CloseoutRun, files: Sequence[SampleFile]) -> None:
        await self._begin(run, "verify", "Running bounded checks")
        shape = execute_tool("validate_submission_shape", files)
        secrets = execute_tool("scan_secrets", files)
        cloud_evidence = self.settings.cloud_runtime_evidence
        checks = shape.evidence["checks"]
        by_name = {item.name.casefold(): item for item in files}
        requirements_text = by_name.get("requirements.md")
        has_taskmaster = bool(
            requirements_text and "taskmaster" in requirements_text.content.casefold()
        )
        has_readme = bool(checks["readme"])
        has_run_instructions = bool(checks["spin_up"])
        has_architecture = bool(checks["architecture"])
        has_video_proof = bool(checks["video_timing"] and checks["public_video"])
        has_cloud_proof = bool(cloud_evidence or checks["cloud_run_proof"])
        evidence_map = {
            "track": (
                ["requirements.md"] if has_taskmaster else [],
                Verdict.VERIFIED if has_taskmaster else Verdict.BLOCKED,
                0.99,
                None if has_taskmaster else "Add the selected Taskmaster track to requirements.md",
            ),
            "description": (
                ["README.md"] if has_readme else [],
                Verdict.VERIFIED if has_readme else Verdict.BLOCKED,
                0.96,
                None if has_readme else "Add an English product description to README.md",
            ),
            "repository": (
                ["README.md#run-locally"] if has_run_instructions else [],
                Verdict.VERIFIED if has_run_instructions else Verdict.BLOCKED,
                0.94,
                None if has_run_instructions else "Add reproducible local run instructions",
            ),
            "architecture": (
                [
                    next(
                        (
                            item.name
                            for item in files
                            if item.name.casefold().endswith((".mmd", ".svg"))
                        ),
                        "",
                    )
                ]
                if has_architecture
                else [],
                Verdict.VERIFIED if has_architecture else Verdict.BLOCKED,
                0.99,
                None if has_architecture else "Add a Mermaid or SVG architecture artifact",
            ),
            "video": (
                ["demo-notes.txt", "public-video-url"]
                if has_video_proof
                else ["demo-notes.txt"]
                if checks["video_timing"]
                else [],
                Verdict.VERIFIED if has_video_proof else Verdict.BLOCKED,
                0.92 if has_video_proof else 0.82,
                None if has_video_proof else "Publish the demo and add its YouTube or Vimeo URL",
            ),
            "cloud": (
                ["deployment.md#runtime-verified" if has_cloud_proof else "deployment.md#pending"],
                Verdict.VERIFIED if has_cloud_proof else Verdict.BLOCKED,
                1.0 if cloud_evidence else 0.92,
                None if has_cloud_proof else "Deploy to Cloud Run and capture the runtime revision",
            ),
            "security": (
                ["scan_secrets:no-matches"],
                Verdict.VERIFIED if secrets.ok else Verdict.BLOCKED,
                1.0,
                None,
            ),
            "ledger": ([], Verdict.BLOCKED, 1.0, "Generate evidence-ledger.json"),
        }
        for requirement in run.requirements:
            evidence, verdict, confidence, action = evidence_map[requirement.id]
            requirement.evidence = evidence
            requirement.verdict = verdict
            requirement.confidence = confidence
            requirement.action = action
        run.metrics.verified = sum(item.verdict == Verdict.VERIFIED for item in run.requirements)
        run.metrics.blocked = sum(item.verdict == Verdict.BLOCKED for item in run.requirements)
        run.metrics.evidence_coverage = round(run.metrics.verified / len(run.requirements) * 100)
        run.metrics.autonomous_actions += 2
        self._event(run, "verify", "Submission gates checked", shape.summary, "verification-kernel")
        self._event(run, "verify", "Credential boundary checked", secrets.summary, "security-tool")
        await self._finish(
            run,
            "verify",
            f"{run.metrics.verified} verified, {run.metrics.blocked} gaps found",
        )

    async def _close(self, run: CloseoutRun, files: Sequence[SampleFile]) -> None:
        await self._begin(run, "close", "Applying reversible repairs")
        for requirement in run.requirements:
            if requirement.id == "video":
                requirement.evidence.append("VIDEO_CAPTIONS.srt")
                if requirement.verdict == Verdict.BLOCKED:
                    requirement.action = "Caption draft generated; public video URL still required"
            elif requirement.id == "ledger":
                requirement.evidence.append("evidence-ledger.json")
                requirement.verdict = Verdict.REPAIRED
                requirement.action = "Generated machine-readable evidence ledger"
        run.generated_artifacts = {
            "VIDEO_CAPTIONS.srt": (
                "1\n00:00:00,000 --> 00:00:28,000\n"
                "Closeout turns last-mile delivery work into an autonomous, "
                "evidence-backed workflow.\n\n"
                "2\n00:00:28,000 --> 00:01:30,000\n"
                "A live run maps requirements, verifies the workspace, repairs gaps, "
                "and seals the bundle.\n"
            ),
            "evidence-ledger.json": json.dumps(
                {
                    "schema_version": 1,
                    "workspace_fingerprint": self._workspace_fingerprint(files),
                    "requirements": [item.model_dump(mode="json") for item in run.requirements],
                },
                indent=2,
                sort_keys=True,
            ),
        }
        run.metrics.repaired = sum(item.verdict == Verdict.REPAIRED for item in run.requirements)
        run.metrics.blocked = sum(item.verdict == Verdict.BLOCKED for item in run.requirements)
        covered = sum(
            item.verdict in {Verdict.VERIFIED, Verdict.REPAIRED} for item in run.requirements
        )
        run.metrics.evidence_coverage = round(covered / len(run.requirements) * 100)
        run.metrics.autonomous_actions += 2
        self._event(
            run,
            "close",
            "Caption artifact generated",
            "Added a timed English caption draft",
            "closeout-agent",
        )
        self._event(
            run,
            "close",
            "Evidence ledger generated",
            "Bound 8 obligations to inspectable artifacts",
            "closeout-agent",
        )
        summary = (
            f"{run.metrics.repaired} gap repaired, {run.metrics.blocked} external gates remain"
        )
        await self._finish(run, "close", summary)

    async def _seal(self, run: CloseoutRun, files: Sequence[SampleFile]) -> None:
        await self._begin(run, "seal", "Hashing closeout bundle")
        manifest = execute_tool("build_manifest", files, run.generated_artifacts)
        run.generated_artifacts["MANIFEST.json"] = str(manifest.evidence["manifest"])
        bundle = self._render_bundle(run, files)
        run.bundle_sha256 = hashlib.sha256(bundle).hexdigest()
        run.bundle_ready = True
        run.metrics.autonomous_actions += 1
        self._event(
            run,
            "seal",
            "Closeout bundle sealed",
            f"SHA-256 {run.bundle_sha256[:16]}...",
            "manifest-tool",
            metadata={
                "sha256": run.bundle_sha256,
                "files": len(files) + len(run.generated_artifacts),
            },
        )
        await self._finish(
            run,
            "seal",
            f"{len(files) + len(run.generated_artifacts)} files sealed",
        )

    async def build_bundle_bytes(self, run: CloseoutRun) -> bytes:
        files = await self.repository.get_files(run.id)
        if not files:
            raise ValueError("Workspace inputs are unavailable")
        return self._render_bundle(run, files)

    def _render_bundle(self, run: CloseoutRun, files: Sequence[SampleFile]) -> bytes:
        if not run.generated_artifacts:
            raise ValueError("Bundle is not ready")
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for item in files:
                self._write_text(archive, item.name, item.content)
            for name, content in sorted(run.generated_artifacts.items()):
                self._write_text(archive, name, content)
        return buffer.getvalue()

    @staticmethod
    def _write_text(archive: zipfile.ZipFile, name: str, content: str) -> None:
        entry = zipfile.ZipInfo(name, date_time=(2026, 8, 3, 0, 0, 0))
        entry.compress_type = zipfile.ZIP_DEFLATED
        entry.external_attr = 0o644 << 16
        archive.writestr(entry, content.encode("utf-8"))

    @staticmethod
    def _workspace_fingerprint(files: Sequence[SampleFile]) -> str:
        digest = hashlib.sha256()
        for item in sorted(files, key=lambda candidate: candidate.name.casefold()):
            digest.update(item.name.encode("utf-8"))
            digest.update(b"\0")
            digest.update(item.content.encode("utf-8"))
            digest.update(b"\0")
        return digest.hexdigest()

    @staticmethod
    def _stage(run: CloseoutRun, stage_id: str) -> Stage:
        return next(stage for stage in run.stages if stage.id == stage_id)

    @staticmethod
    def _reset_for_retry(run: CloseoutRun, previous_status: RunStatus) -> None:
        run.stages = [Stage(id=key, label=label) for key, label in STAGES]
        run.artifacts = []
        run.requirements = []
        run.metrics = RunMetrics()
        run.generated_artifacts = {}
        run.planned_actions = []
        run.bundle_ready = False
        run.bundle_sha256 = None
        CloseoutWorkflow._event(
            run,
            "system",
            "Workflow retry started",
            f"Reset deterministic outputs after {previous_status.value}",
            "execution-kernel",
        )

    @staticmethod
    def _event(
        run: CloseoutRun,
        stage: str,
        title: str,
        detail: str,
        actor: str,
        status: StageStatus = StageStatus.COMPLETED,
        metadata: dict[str, object] | None = None,
    ) -> None:
        run.events.append(
            TimelineEvent(
                id=uuid.uuid4().hex[:10],
                stage=stage,
                title=title,
                detail=detail,
                actor=actor,
                status=status,
                metadata=metadata or {},
            )
        )


def summarize_runs(runs: Sequence[CloseoutRun]) -> list[CloseoutRun]:
    return list(runs)
