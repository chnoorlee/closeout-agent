from __future__ import annotations

from pathlib import PurePosixPath

from fastapi import HTTPException, UploadFile

from backend.app.sample_data import SampleFile

ALLOWED_SUFFIXES = {".csv", ".json", ".md", ".mmd", ".svg", ".txt", ".yaml", ".yml"}
MAX_FILES = 8
MAX_FILE_BYTES = 128 * 1024
MAX_TOTAL_BYTES = 384 * 1024


async def read_workspace_uploads(uploads: list[UploadFile]) -> tuple[SampleFile, ...]:
    if not uploads:
        raise HTTPException(status_code=422, detail="At least one workspace file is required")
    if len(uploads) > MAX_FILES:
        raise HTTPException(
            status_code=413, detail=f"A workspace can contain at most {MAX_FILES} files"
        )

    files: list[SampleFile] = []
    seen: set[str] = set()
    total_bytes = 0
    for upload in uploads:
        raw_name = upload.filename or ""
        normalized = raw_name.replace("\\", "/")
        name = PurePosixPath(normalized).name
        if not name or normalized != name:
            raise HTTPException(
                status_code=400, detail="Workspace filenames must not contain paths"
            )
        if PurePosixPath(name).suffix.lower() not in ALLOWED_SUFFIXES:
            raise HTTPException(status_code=415, detail=f"Unsupported workspace file: {name}")
        if name.casefold() in seen:
            raise HTTPException(status_code=409, detail=f"Duplicate workspace filename: {name}")

        raw = await upload.read(MAX_FILE_BYTES + 1)
        if len(raw) > MAX_FILE_BYTES:
            raise HTTPException(status_code=413, detail=f"Workspace file exceeds 128 KiB: {name}")
        total_bytes += len(raw)
        if total_bytes > MAX_TOTAL_BYTES:
            raise HTTPException(status_code=413, detail="Workspace exceeds the 384 KiB limit")
        try:
            content = raw.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=415, detail=f"Workspace file is not UTF-8 text: {name}"
            ) from exc
        if "\x00" in content:
            raise HTTPException(
                status_code=415, detail=f"Workspace file contains binary data: {name}"
            )

        seen.add(name.casefold())
        files.append(
            SampleFile(
                name=name,
                media_type=upload.content_type or "text/plain",
                content=content,
            )
        )
    return tuple(files)
