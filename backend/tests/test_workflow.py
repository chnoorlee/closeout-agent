import asyncio
import hashlib
import io
import json
import zipfile

import pytest

from backend.app.config import Settings
from backend.app.domain import RunStatus, Verdict
from backend.app.repository import MemoryRunRepository
from backend.app.sample_data import build_sample_files
from backend.app.tools import execute_tool
from backend.app.workflow import CloseoutWorkflow


@pytest.mark.asyncio
async def test_local_demo_preserves_external_cloud_blocker_and_seals_bundle() -> None:
    settings = Settings(
        CLOSEOUT_STORE="memory",
        CLOSEOUT_DISPATCHER="local",
        CLOSEOUT_DEMO_MODE=True,
        CLOSEOUT_STAGE_DELAY_MS=0,
    )
    repository = MemoryRunRepository()
    workflow = CloseoutWorkflow(repository, settings)

    created = await workflow.create_demo_run("hackathon-closeout")
    await workflow.process(created.id)
    run = await repository.get(created.id)

    assert run is not None
    assert run.status == RunStatus.COMPLETED
    assert run.metrics.evidence_coverage == 75
    assert run.metrics.repaired == 1
    assert run.metrics.blocked == 2
    cloud = next(item for item in run.requirements if item.id == "cloud")
    assert cloud.verdict == Verdict.BLOCKED
    assert cloud.evidence == ["deployment.md#pending"]
    assert run.bundle_ready is True
    assert run.planned_actions == [
        "inventory_workspace",
        "scan_secrets",
        "validate_submission_shape",
        "build_manifest",
    ]

    bundle = await workflow.build_bundle_bytes(run)
    assert hashlib.sha256(bundle).hexdigest() == run.bundle_sha256
    with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
        assert "MANIFEST.json" in archive.namelist()
        assert "evidence-ledger.json" in archive.namelist()
        assert "VIDEO_CAPTIONS.srt" in archive.namelist()
        ledger = json.loads(archive.read("evidence-ledger.json"))
        blocked = [item for item in ledger["requirements"] if item["verdict"] == "blocked"]
        assert [item["id"] for item in blocked] == ["video", "cloud"]

    fresh_worker = CloseoutWorkflow(repository, settings)
    assert await fresh_worker.build_bundle_bytes(run) == bundle


@pytest.mark.asyncio
async def test_cloud_runtime_evidence_closes_external_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("K_SERVICE", "closeout")
    monkeypatch.setenv("K_REVISION", "closeout-00001-abc")
    settings = Settings(
        CLOSEOUT_STORE="memory",
        CLOSEOUT_DISPATCHER="local",
        CLOSEOUT_STAGE_DELAY_MS=0,
    )
    repository = MemoryRunRepository()
    workflow = CloseoutWorkflow(repository, settings)

    created = await workflow.create_demo_run("hackathon-closeout")
    await workflow.process(created.id)
    run = await repository.get(created.id)

    assert run is not None
    assert run.metrics.evidence_coverage == 88
    assert run.metrics.blocked == 1
    cloud = next(item for item in run.requirements if item.id == "cloud")
    assert cloud.verdict == Verdict.VERIFIED
    assert cloud.evidence == ["deployment.md#runtime-verified"]


@pytest.mark.asyncio
async def test_processing_is_idempotent_after_completion() -> None:
    settings = Settings(CLOSEOUT_STAGE_DELAY_MS=0)
    repository = MemoryRunRepository()
    workflow = CloseoutWorkflow(repository, settings)
    run = await workflow.create_demo_run("hackathon-closeout")

    await workflow.process(run.id)
    first = await repository.get(run.id)
    await workflow.process(run.id)
    second = await repository.get(run.id)

    assert first is not None and second is not None
    assert len(second.events) == len(first.events)
    assert second.bundle_sha256 == first.bundle_sha256


@pytest.mark.asyncio
async def test_concurrent_delivery_claim_executes_workflow_once() -> None:
    settings = Settings(CLOSEOUT_STAGE_DELAY_MS=10)
    repository = MemoryRunRepository()
    workflow = CloseoutWorkflow(repository, settings)
    run = await workflow.create_demo_run("hackathon-closeout")

    await asyncio.gather(workflow.process(run.id), workflow.process(run.id))
    completed = await repository.get(run.id)

    assert completed is not None and completed.status == RunStatus.COMPLETED
    assert sum(event.title == "Workspace fingerprinted" for event in completed.events) == 1


@pytest.mark.asyncio
async def test_identical_inputs_produce_identical_bundle_bytes() -> None:
    settings = Settings(CLOSEOUT_STAGE_DELAY_MS=0)
    repository = MemoryRunRepository()
    workflow = CloseoutWorkflow(repository, settings)
    first_run = await workflow.create_demo_run("hackathon-closeout")
    second_run = await workflow.create_demo_run("hackathon-closeout")

    await workflow.process(first_run.id)
    await workflow.process(second_run.id)
    first = await repository.get(first_run.id)
    second = await repository.get(second_run.id)

    assert first is not None and second is not None
    assert await workflow.build_bundle_bytes(first) == await workflow.build_bundle_bytes(second)


def test_tool_executor_rejects_non_allowlisted_action() -> None:
    with pytest.raises(ValueError, match="not allowlisted"):
        execute_tool("run_shell", ())


@pytest.mark.asyncio
async def test_failed_run_retries_from_persisted_inputs() -> None:
    settings = Settings(CLOSEOUT_STAGE_DELAY_MS=0)
    repository = MemoryRunRepository()
    workflow = CloseoutWorkflow(repository, settings)
    run = await workflow.create_demo_run("hackathon-closeout")
    await repository.save_files(run.id, ())

    with pytest.raises(RuntimeError, match="inputs are unavailable"):
        await workflow.process(run.id)
    failed = await repository.get(run.id)
    assert failed is not None and failed.status == RunStatus.FAILED

    await repository.save_files(run.id, build_sample_files(settings))
    await workflow.process(run.id)
    recovered = await repository.get(run.id)

    assert recovered is not None and recovered.status == RunStatus.COMPLETED
    assert any(event.title == "Workflow retry started" for event in recovered.events)
