from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from backend.app.config import Settings

logger = logging.getLogger(__name__)


class Dispatcher:
    name: str

    async def dispatch(self, run_id: str) -> None: ...


class LocalDispatcher(Dispatcher):
    name = "local-background-task"

    def __init__(self, processor: Callable[[str], Coroutine[Any, Any, None]]) -> None:
        self._processor = processor
        self._tasks: set[asyncio.Task[None]] = set()

    async def dispatch(self, run_id: str) -> None:
        task: asyncio.Task[None] = asyncio.create_task(
            self._processor(run_id), name=f"closeout-{run_id}"
        )
        self._tasks.add(task)
        task.add_done_callback(self._task_finished)

    def _task_finished(self, task: asyncio.Task[None]) -> None:
        self._tasks.discard(task)
        if task.cancelled():
            return
        error = task.exception()
        if error:
            logger.error("Local closeout task failed: %s", error)


class CloudTasksDispatcher(Dispatcher):
    name = "google-cloud-tasks"

    def __init__(self, settings: Settings) -> None:
        from google.cloud import tasks_v2

        if not settings.google_cloud_project or not settings.service_url:
            raise ValueError("Cloud Tasks requires project and service URL")
        self._settings = settings
        self._client = tasks_v2.CloudTasksClient()
        self._parent = self._client.queue_path(
            settings.google_cloud_project, settings.tasks_location, settings.tasks_queue
        )

    async def dispatch(self, run_id: str) -> None:
        from google.cloud import tasks_v2

        assert self._settings.service_url
        assert self._settings.google_cloud_project
        headers = {"Content-Type": "application/json"}
        if self._settings.task_secret:
            headers["X-Closeout-Task-Secret"] = self._settings.task_secret
        request = tasks_v2.HttpRequest(
            http_method=tasks_v2.HttpMethod.POST,
            url=f"{self._settings.service_url.rstrip('/')}/api/tasks/execute",
            headers=headers,
            body=json.dumps({"run_id": run_id}).encode(),
        )
        if self._settings.task_service_account:
            request.oidc_token = tasks_v2.OidcToken(
                service_account_email=self._settings.task_service_account,
                audience=self._settings.service_url,
            )
        task = tasks_v2.Task(
            name=self._client.task_path(
                self._settings.google_cloud_project,
                self._settings.tasks_location,
                self._settings.tasks_queue,
                f"run-{run_id}",
            ),
            http_request=request,
        )
        await asyncio.to_thread(self._client.create_task, parent=self._parent, task=task)
