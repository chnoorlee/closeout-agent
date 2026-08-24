import io
import time
import zipfile
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.dispatcher import Dispatcher
from backend.app.main import create_app, resolve_static_file


def test_static_file_resolution_cannot_escape_root(tmp_path: Path) -> None:
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    asset = static_dir / "asset.txt"
    asset.write_text("public", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("private", encoding="utf-8")

    assert resolve_static_file(static_dir, "asset.txt") == asset
    assert resolve_static_file(static_dir, "missing.txt") is None
    with pytest.raises(HTTPException) as error:
        resolve_static_file(static_dir, "../secret.txt")
    assert error.value.status_code == 404


def test_public_cloud_tasks_runtime_omits_worker_route(monkeypatch: pytest.MonkeyPatch) -> None:
    class StubCloudDispatcher(Dispatcher):
        name = "google-cloud-tasks"

        async def dispatch(self, run_id: str) -> None:
            del run_id

    monkeypatch.setattr(
        "backend.app.main.CloudTasksDispatcher", lambda settings: StubCloudDispatcher()
    )
    settings = Settings(
        environment="production",
        CLOSEOUT_STORE="memory",
        CLOSEOUT_DISPATCHER="cloud-tasks",
        GOOGLE_CLOUD_PROJECT="example-project",
        CLOSEOUT_SERVICE_URL="https://worker.example.com",
        CLOSEOUT_STAGE_DELAY_MS=0,
    )

    app = create_app(settings)

    assert "/api/tasks/execute" not in app.openapi()["paths"]


def test_health_discloses_demo_mode() -> None:
    app = create_app(
        Settings(
            environment="test",
            CLOSEOUT_STORE="memory",
            CLOSEOUT_DISPATCHER="local",
            CLOSEOUT_STAGE_DELAY_MS=0,
        )
    )
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["ai_mode"] == "deterministic-demo"
    assert response.json()["framework"] == "Google ADK 2"


def test_demo_run_reaches_downloadable_bundle() -> None:
    app = create_app(
        Settings(
            environment="test",
            CLOSEOUT_STORE="memory",
            CLOSEOUT_DISPATCHER="local",
            CLOSEOUT_STAGE_DELAY_MS=0,
        )
    )
    with TestClient(app) as client:
        created = client.post("/api/runs/demo", json={"scenario": "hackathon-closeout"})
        assert created.status_code == 202
        run_id = created.json()["id"]
        deadline = time.monotonic() + 2
        payload = created.json()
        while payload["status"] not in {"completed", "failed"} and time.monotonic() < deadline:
            payload = client.get(f"/api/runs/{run_id}").json()
        assert payload["status"] == "completed"
        bundle = client.get(f"/api/runs/{run_id}/bundle")

    assert bundle.status_code == 200
    assert bundle.headers["content-type"] == "application/zip"
    assert len(bundle.content) > 500


def test_uploaded_workspace_is_processed_and_preserved_in_bundle() -> None:
    app = create_app(
        Settings(
            environment="test",
            CLOSEOUT_STORE="memory",
            CLOSEOUT_DISPATCHER="local",
            CLOSEOUT_STAGE_DELAY_MS=0,
        )
    )
    uploads = [
        (
            "files",
            ("README.md", b"# Real input\n\n## Run locally\nuv run uvicorn", "text/markdown"),
        ),
        (
            "files",
            ("requirements.md", b"# Requirements\n\nTrack: Taskmaster", "text/markdown"),
        ),
        ("files", ("architecture.mmd", b"flowchart LR\nA --> B", "text/plain")),
    ]
    with TestClient(app) as client:
        created = client.post("/api/runs", data={"name": "Real delivery"}, files=uploads)
        assert created.status_code == 202
        assert "content" not in created.text
        run_id = created.json()["id"]
        deadline = time.monotonic() + 2
        payload = created.json()
        while payload["status"] not in {"completed", "failed"} and time.monotonic() < deadline:
            payload = client.get(f"/api/runs/{run_id}").json()
        bundle = client.get(f"/api/runs/{run_id}/bundle")

    assert payload["status"] == "completed"
    assert payload["name"] == "Real delivery / Closeout"
    with zipfile.ZipFile(io.BytesIO(bundle.content)) as archive:
        assert archive.read("README.md").startswith(b"# Real input")


def test_uploaded_workspace_rejects_paths_and_binary_files() -> None:
    app = create_app(Settings(environment="test", CLOSEOUT_STAGE_DELAY_MS=0))
    with TestClient(app) as client:
        traversal = client.post(
            "/api/runs",
            files={"files": ("../README.md", b"# escaped", "text/markdown")},
        )
        binary = client.post(
            "/api/runs",
            files={"files": ("artifact.txt", b"abc\x00def", "text/plain")},
        )

    assert traversal.status_code == 400
    assert binary.status_code == 415
