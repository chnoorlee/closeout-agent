from __future__ import annotations

import hmac
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.app.config import Settings, get_settings
from backend.app.dispatcher import CloudTasksDispatcher, Dispatcher, LocalDispatcher
from backend.app.domain import CloseoutRun, CreateDemoRun, HealthResponse
from backend.app.intake import read_workspace_uploads
from backend.app.repository import FirestoreRunRepository, MemoryRunRepository, RunRepository
from backend.app.workflow import CloseoutWorkflow


class TaskPayload(BaseModel):
    run_id: str


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Closeout API", version="0.1.0")

    repository: RunRepository
    use_firestore = settings.store == "firestore" or (
        settings.store == "auto"
        and settings.environment == "production"
        and settings.google_cloud_project
    )
    repository = (
        FirestoreRunRepository(settings.google_cloud_project)
        if use_firestore
        else MemoryRunRepository()
    )
    workflow = CloseoutWorkflow(repository, settings)

    use_cloud_tasks = settings.dispatcher == "cloud-tasks" or (
        settings.dispatcher == "auto"
        and settings.environment == "production"
        and settings.service_url
    )
    dispatcher: Dispatcher = (
        CloudTasksDispatcher(settings) if use_cloud_tasks else LocalDispatcher(workflow.process)
    )

    app.state.settings = settings
    app.state.repository = repository
    app.state.workflow = workflow
    app.state.dispatcher = dispatcher

    def get_repository() -> RunRepository:
        return repository

    def get_workflow() -> CloseoutWorkflow:
        return workflow

    def get_dispatcher() -> Dispatcher:
        return dispatcher

    @app.get("/api/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            service=settings.app_name,
            model=settings.model,
            framework="Google ADK 2",
            ai_mode="live-gemini" if settings.has_live_ai_config else "deterministic-demo",
            store=repository.name,
            dispatcher=dispatcher.name,
        )

    @app.get("/api/runs", response_model=list[CloseoutRun])
    async def list_runs(repo: RunRepository = Depends(get_repository)) -> list[CloseoutRun]:
        return list(await repo.list())

    @app.post("/api/runs/demo", response_model=CloseoutRun, status_code=202)
    async def create_demo(
        request: CreateDemoRun,
        engine: CloseoutWorkflow = Depends(get_workflow),
        task_dispatcher: Dispatcher = Depends(get_dispatcher),
    ) -> CloseoutRun:
        run = await engine.create_demo_run(request.scenario)
        await task_dispatcher.dispatch(run.id)
        return run

    @app.post("/api/runs", response_model=CloseoutRun, status_code=202)
    async def create_workspace(
        files: list[UploadFile] = File(...),
        name: str = Form("Uploaded workspace"),
        engine: CloseoutWorkflow = Depends(get_workflow),
        task_dispatcher: Dispatcher = Depends(get_dispatcher),
    ) -> CloseoutRun:
        normalized_name = name.strip()
        if not normalized_name or len(normalized_name) > 80:
            raise HTTPException(status_code=422, detail="Workspace name must be 1 to 80 characters")
        inputs = await read_workspace_uploads(files)
        run = await engine.create_workspace_run(normalized_name, inputs)
        await task_dispatcher.dispatch(run.id)
        return run

    @app.get("/api/runs/{run_id}", response_model=CloseoutRun)
    async def get_run(
        run_id: str,
        repo: RunRepository = Depends(get_repository),
    ) -> CloseoutRun:
        run = await repo.get(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        return run

    @app.get("/api/runs/{run_id}/bundle")
    async def download_bundle(
        run_id: str,
        repo: RunRepository = Depends(get_repository),
        engine: CloseoutWorkflow = Depends(get_workflow),
    ) -> Response:
        run = await repo.get(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        if not run.bundle_ready:
            raise HTTPException(status_code=409, detail="Bundle is not ready")
        return Response(
            content=await engine.build_bundle_bytes(run),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="closeout-{run.id}.zip"'},
        )

    @app.post("/api/tasks/execute", status_code=202)
    async def execute_task(
        payload: TaskPayload,
        x_closeout_task_secret: str | None = Header(default=None),
        engine: CloseoutWorkflow = Depends(get_workflow),
    ) -> dict[str, str]:
        if settings.task_secret and not hmac.compare_digest(
            x_closeout_task_secret or "", settings.task_secret
        ):
            raise HTTPException(status_code=401, detail="Invalid task credential")
        await engine.process(payload.run_id)
        return {"status": "accepted", "run_id": payload.run_id}

    static_dir = Path(__file__).resolve().parents[1] / "static"
    if static_dir.exists():
        assets_dir = static_dir / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        async def spa(path: str) -> FileResponse:
            target = static_dir / path
            if path and target.is_file():
                return FileResponse(target)
            return FileResponse(static_dir / "index.html")

    return app


app = create_app()
