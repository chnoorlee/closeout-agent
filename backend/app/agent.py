from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.app.config import Settings

SYSTEM_CONTRACT = """You are Closeout, an autonomous last-mile delivery agent.
Your job is to map explicit requirements to inspectable evidence, identify gaps,
and select only bounded, reversible actions. Never claim that an external URL,
deployment, approval, or test passed unless the supplied evidence says so.
Each proposed action must be one of: inventory_workspace, scan_secrets,
validate_submission_shape, build_manifest.
"""


class AgentAnalysis(BaseModel):
    summary: str = Field(min_length=1, max_length=800)
    requirements: list[str] = Field(default_factory=list, max_length=20)
    risks: list[str] = Field(default_factory=list, max_length=20)
    proposed_actions: list[
        Literal[
            "inventory_workspace",
            "scan_secrets",
            "validate_submission_shape",
            "build_manifest",
        ]
    ] = Field(default_factory=list, max_length=8)


async def analyze_with_adk(
    settings: Settings, run_id: str, evidence_payload: dict[str, Any]
) -> dict[str, Any]:
    """Run the live Gemini analysis through Google ADK.

    Imports are intentionally lazy so the deterministic demo stays runnable
    without cloud credentials while preserving an auditable live path.
    """
    from google.adk.agents import Agent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    agent = Agent(
        name="closeout_taskmaster",
        model=settings.model,
        description="Maps delivery requirements to evidence and bounded closeout actions.",
        instruction=SYSTEM_CONTRACT,
        output_schema=AgentAnalysis,
    )
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name="closeout", user_id="workspace-owner", session_id=run_id
    )
    runner = Runner(agent=agent, app_name="closeout", session_service=session_service)
    message = types.Content(
        role="user",
        parts=[types.Part(text=json.dumps(evidence_payload, sort_keys=True))],
    )
    final_text = ""
    async for event in runner.run_async(
        user_id="workspace-owner", session_id=run_id, new_message=message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = "".join(part.text or "" for part in event.content.parts)
    if not final_text:
        raise RuntimeError("Google ADK returned no final response")
    return AgentAnalysis.model_validate_json(final_text).model_dump()
