from __future__ import annotations

import asyncio
from threading import get_ident
from typing import Any

from google.cloud import tasks_v2

from backend.app.config import Settings
from backend.app.dispatcher import CloudTasksDispatcher


def test_cloud_tasks_client_can_dispatch_after_construction_outside_event_loop(
    monkeypatch: Any,
) -> None:
    calls: list[dict[str, Any]] = []
    constructor_thread = get_ident()

    class StubCloudTasksClient:
        @staticmethod
        def queue_path(project: str, location: str, queue: str) -> str:
            return f"projects/{project}/locations/{location}/queues/{queue}"

        @staticmethod
        def task_path(project: str, location: str, queue: str, task: str) -> str:
            return f"projects/{project}/locations/{location}/queues/{queue}/tasks/{task}"

        @staticmethod
        def create_task(*, parent: str, task: tasks_v2.Task) -> None:
            calls.append({"parent": parent, "task": task, "thread": get_ident()})

    monkeypatch.setattr(tasks_v2, "CloudTasksClient", StubCloudTasksClient)
    settings = Settings(
        environment="production",
        GOOGLE_CLOUD_PROJECT="example-project",
        CLOSEOUT_SERVICE_URL="https://worker.example.com",
        CLOSEOUT_TASK_SERVICE_ACCOUNT="task@example-project.iam.gserviceaccount.com",
    )
    dispatcher = CloudTasksDispatcher(settings)

    asyncio.run(dispatcher.dispatch("abc123"))

    assert len(calls) == 1
    assert calls[0]["parent"].endswith("/queues/closeout-runs")
    assert calls[0]["task"].name.endswith("/tasks/run-abc123")
    assert calls[0]["task"].http_request.url == "https://worker.example.com/api/tasks/execute"
    assert calls[0]["thread"] != constructor_thread
