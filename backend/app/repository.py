from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import timedelta
from typing import Any

from backend.app.domain import CloseoutRun, RunStatus, utc_now
from backend.app.sample_data import SampleFile


class RunRepository(ABC):
    name: str

    @abstractmethod
    async def create(self, run: CloseoutRun) -> CloseoutRun: ...

    @abstractmethod
    async def get(self, run_id: str) -> CloseoutRun | None: ...

    @abstractmethod
    async def claim(
        self, run_id: str, lease_timeout: timedelta
    ) -> tuple[CloseoutRun, RunStatus] | None: ...

    @abstractmethod
    async def save(self, run: CloseoutRun) -> CloseoutRun: ...

    @abstractmethod
    async def list(self, limit: int = 20) -> Sequence[CloseoutRun]: ...

    @abstractmethod
    async def save_files(self, run_id: str, files: Sequence[SampleFile]) -> None: ...

    @abstractmethod
    async def get_files(self, run_id: str) -> tuple[SampleFile, ...]: ...


class MemoryRunRepository(RunRepository):
    name = "memory"

    def __init__(self) -> None:
        self._runs: dict[str, CloseoutRun] = {}
        self._files: dict[str, tuple[SampleFile, ...]] = {}
        self._lock = asyncio.Lock()

    async def create(self, run: CloseoutRun) -> CloseoutRun:
        async with self._lock:
            if run.id in self._runs:
                return self._runs[run.id].model_copy(deep=True)
            self._runs[run.id] = run.model_copy(deep=True)
            return run.model_copy(deep=True)

    async def get(self, run_id: str) -> CloseoutRun | None:
        async with self._lock:
            run = self._runs.get(run_id)
            return run.model_copy(deep=True) if run else None

    async def claim(
        self, run_id: str, lease_timeout: timedelta
    ) -> tuple[CloseoutRun, RunStatus] | None:
        async with self._lock:
            stored = self._runs.get(run_id)
            if not stored or stored.status == RunStatus.COMPLETED:
                return None
            if (
                stored.status == RunStatus.RUNNING
                and utc_now() - stored.updated_at < lease_timeout
            ):
                return None
            previous_status = stored.status
            claimed = stored.model_copy(deep=True)
            claimed.status = RunStatus.RUNNING
            claimed.error = None
            claimed.updated_at = utc_now()
            self._runs[run_id] = claimed.model_copy(deep=True)
            return claimed, previous_status

    async def save(self, run: CloseoutRun) -> CloseoutRun:
        async with self._lock:
            run.updated_at = utc_now()
            self._runs[run.id] = run.model_copy(deep=True)
            return run.model_copy(deep=True)

    async def list(self, limit: int = 20) -> Sequence[CloseoutRun]:
        async with self._lock:
            runs = sorted(self._runs.values(), key=lambda item: item.created_at, reverse=True)
            return [run.model_copy(deep=True) for run in runs[:limit]]

    async def save_files(self, run_id: str, files: Sequence[SampleFile]) -> None:
        async with self._lock:
            self._files[run_id] = tuple(files)

    async def get_files(self, run_id: str) -> tuple[SampleFile, ...]:
        async with self._lock:
            return self._files.get(run_id, ())


class FirestoreRunRepository(RunRepository):
    name = "firestore"

    def __init__(self, project: str | None = None) -> None:
        from google.cloud import firestore

        self._client = firestore.AsyncClient(project=project)
        self._collection = self._client.collection("closeout_runs")
        self._inputs = self._client.collection("closeout_run_inputs")

    async def create(self, run: CloseoutRun) -> CloseoutRun:
        ref = self._collection.document(run.id)
        snapshot = await ref.get()
        if snapshot.exists:
            return CloseoutRun.model_validate(snapshot.to_dict())
        await ref.set(run.model_dump(mode="json"))
        return run

    async def get(self, run_id: str) -> CloseoutRun | None:
        snapshot = await self._collection.document(run_id).get()
        if not snapshot.exists:
            return None
        return CloseoutRun.model_validate(snapshot.to_dict())

    async def claim(
        self, run_id: str, lease_timeout: timedelta
    ) -> tuple[CloseoutRun, RunStatus] | None:
        from google.cloud import firestore

        ref = self._collection.document(run_id)

        @firestore.async_transactional
        async def claim_in_transaction(
            transaction: Any,
        ) -> tuple[CloseoutRun, RunStatus] | None:
            snapshot = await ref.get(transaction=transaction)
            if not snapshot.exists:
                return None
            run = CloseoutRun.model_validate(snapshot.to_dict())
            if run.status == RunStatus.COMPLETED:
                return None
            if run.status == RunStatus.RUNNING and utc_now() - run.updated_at < lease_timeout:
                return None
            previous_status = run.status
            run.status = RunStatus.RUNNING
            run.error = None
            run.updated_at = utc_now()
            transaction.set(ref, run.model_dump(mode="json"))
            return run, previous_status

        return await claim_in_transaction(self._client.transaction())

    async def save(self, run: CloseoutRun) -> CloseoutRun:
        run.updated_at = utc_now()
        await self._collection.document(run.id).set(run.model_dump(mode="json"))
        return run

    async def list(self, limit: int = 20) -> Sequence[CloseoutRun]:
        from google.cloud.firestore_v1 import Query

        query = self._collection.order_by("created_at", direction=Query.DESCENDING).limit(limit)
        return [CloseoutRun.model_validate(item.to_dict()) async for item in query.stream()]

    async def save_files(self, run_id: str, files: Sequence[SampleFile]) -> None:
        payload = {
            "files": [
                {"name": item.name, "media_type": item.media_type, "content": item.content}
                for item in files
            ]
        }
        await self._inputs.document(run_id).set(payload)

    async def get_files(self, run_id: str) -> tuple[SampleFile, ...]:
        snapshot = await self._inputs.document(run_id).get()
        if not snapshot.exists:
            return ()
        data = snapshot.to_dict() or {}
        return tuple(SampleFile(**item) for item in data.get("files", []))
