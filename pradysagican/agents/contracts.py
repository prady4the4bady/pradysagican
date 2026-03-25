"""Typed contracts for inter-agent communication and orchestration."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OrchestratorRequest(BaseModel):
    task: str
    context: list[str] = Field(default_factory=list)
    priority: int = 5
    session_id: str = "default"


class StrategistResponse(BaseModel):
    plan: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    estimated_steps: int = 0
    rationale: str = ""


class AgentTaskEnvelope(BaseModel):
    task_id: str
    role: str
    payload: dict


class AgentResultEnvelope(BaseModel):
    task_id: str
    role: str
    success: bool
    result: dict = Field(default_factory=dict)
    error: str = ""
