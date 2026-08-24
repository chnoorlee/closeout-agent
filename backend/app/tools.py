from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from backend.app.sample_data import SampleFile


@dataclass(frozen=True)
class ToolResult:
    tool: str
    ok: bool
    summary: str
    evidence: dict[str, Any]


def inventory_workspace(files: Sequence[SampleFile]) -> ToolResult:
    """Inventory bounded workspace files and compute content hashes."""
    inventory = [
        {
            "name": item.name,
            "bytes": len(item.content.encode("utf-8")),
            "sha256": hashlib.sha256(item.content.encode("utf-8")).hexdigest(),
        }
        for item in files
    ]
    return ToolResult(
        "inventory_workspace",
        True,
        f"Indexed {len(inventory)} artifacts",
        {"files": inventory},
    )


def scan_secrets(files: Sequence[SampleFile]) -> ToolResult:
    """Scan text artifacts for common credential patterns without exposing values."""
    patterns = {
        "google_api_key": re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
        "private_key": re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
        "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    }
    matches = []
    for item in files:
        for label, pattern in patterns.items():
            if pattern.search(item.content):
                matches.append({"file": item.name, "type": label})
    return ToolResult(
        "scan_secrets",
        not matches,
        (
            "No credential patterns detected"
            if not matches
            else f"Detected {len(matches)} secret patterns"
        ),
        {"matches": matches},
    )


def validate_submission_shape(files: Sequence[SampleFile]) -> ToolResult:
    """Check that the workspace contains reproducibility, architecture, and cloud proof."""
    by_name = {item.name.casefold(): item.content.lower() for item in files}
    video_proof = "\n".join(
        content for name, content in by_name.items() if "video" in name or "demo" in name
    )
    checks = {
        "readme": "readme.md" in by_name,
        "spin_up": "readme.md" in by_name and "run locally" in by_name["readme.md"],
        "architecture": any(name.endswith((".mmd", ".svg")) for name in by_name),
        "cloud_run_proof": (
            "deployment.md" in by_name
            and "platform: google cloud run" in by_name["deployment.md"]
            and "status: runtime-verified" in by_name["deployment.md"]
        ),
        "video_timing": "demo-notes.txt" in by_name and "03:" in by_name["demo-notes.txt"],
        "public_video": bool(
            re.search(r"https://(?:www\.)?(?:youtube\.com|youtu\.be|vimeo\.com)/", video_proof)
        ),
    }
    return ToolResult(
        "validate_submission_shape",
        all(checks.values()),
        f"{sum(checks.values())}/{len(checks)} submission gates present",
        {"checks": checks},
    )


def build_manifest(files: Sequence[SampleFile], generated: dict[str, str]) -> ToolResult:
    """Build a deterministic manifest for source and generated artifacts."""
    entries = []
    for item in files:
        content = item.content.encode("utf-8")
        entries.append(
            {
                "path": item.name,
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    for name, value in sorted(generated.items()):
        content = value.encode("utf-8")
        entries.append(
            {
                "path": name,
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    payload = json.dumps({"schema_version": 1, "files": entries}, indent=2, sort_keys=True)
    return ToolResult(
        "build_manifest",
        True,
        f"Manifested {len(entries)} files",
        {"manifest": payload},
    )


ALLOWED_TOOLS: dict[str, Callable[..., ToolResult]] = {
    "inventory_workspace": inventory_workspace,
    "scan_secrets": scan_secrets,
    "validate_submission_shape": validate_submission_shape,
    "build_manifest": build_manifest,
}


def execute_tool(
    name: str,
    files: Sequence[SampleFile],
    generated: dict[str, str] | None = None,
) -> ToolResult:
    tool = ALLOWED_TOOLS.get(name)
    if tool is None:
        raise ValueError(f"Tool is not allowlisted: {name}")
    if name == "build_manifest":
        return tool(files, generated or {})
    return tool(files)
