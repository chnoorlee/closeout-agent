import io
import time
import zipfile

from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.main import create_app


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
