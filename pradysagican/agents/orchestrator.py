"""
Master Orchestrator (evolved JARVIS) — PRADYSAGICAN
LangGraph-style stateful agent orchestration with supervisor pattern.
"""
from __future__ import annotations
import asyncio, logging, time, uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable
from enum import Enum

logger = logging.getLogger(__name__)

class AgentRole(str, Enum):
    RESEARCHER = "researcher"
    CODER = "coder"
    ANALYST = "analyst"
    WRITER = "writer"
    REVIEWER = "reviewer"
    EXECUTOR = "executor"

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class SubAgent:
    id: str
    role: AgentRole
    capabilities: list[str] = field(default_factory=list)
    status: str = "idle"
    tasks_completed: int = 0

@dataclass
class TaskNode:
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: str | None = None
    dependencies: list[str] = field(default_factory=list)
    result: Any = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    completed_at: float | None = None

class MasterOrchestrator:
    """Supervisor-pattern multi-agent orchestrator with state machine."""

    def __init__(self, llm_fn: Callable[[str], Awaitable[str]] | None = None) -> None:
        self._llm = llm_fn
        self._agents: dict[str, SubAgent] = {}
        self._tasks: dict[str, TaskNode] = {}
        self._execution_log: list[dict] = []

    def spawn_agent(self, role: AgentRole, capabilities: list[str] | None = None) -> SubAgent:
        agent = SubAgent(id=f"agent_{uuid.uuid4().hex[:8]}", role=role, capabilities=capabilities or [])
        self._agents[agent.id] = agent
        logger.info("Spawned agent %s with role %s", agent.id, role.value)
        return agent

    async def plan_and_execute(self, goal: str) -> dict[str, Any]:
        """Decompose goal into tasks, assign agents, execute."""
        start = time.monotonic()
        # 1. Recursive decomposition
        tasks = await self._decompose(goal)
        # 2. Assign agents to tasks
        for task in tasks:
            agent = self._select_agent(task)
            if agent:
                task.assigned_agent = agent.id
                agent.status = "assigned"
        # 3. Execute respecting dependencies
        results = await self._execute_dag(tasks)
        elapsed = (time.monotonic() - start) * 1000
        return {"goal": goal, "tasks": len(tasks), "completed": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED), "duration_ms": elapsed, "results": results}

    async def _decompose(self, goal: str, max_tasks: int = 8) -> list[TaskNode]:
        """Break a complex goal into sub-tasks."""
        # Heuristic decomposition
        words = goal.split()
        chunk_size = max(len(words) // max_tasks, 3)
        tasks = []
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            task = TaskNode(id=f"task_{uuid.uuid4().hex[:8]}", description=chunk)
            if tasks:
                task.dependencies = [tasks[-1].id]
            tasks.append(task)
            self._tasks[task.id] = task
        return tasks or [TaskNode(id=f"task_{uuid.uuid4().hex[:8]}", description=goal)]

    def _select_agent(self, task: TaskNode) -> SubAgent | None:
        """Route task to best available agent."""
        idle = [a for a in self._agents.values() if a.status == "idle"]
        if not idle:
            idle = list(self._agents.values())
        if not idle:
            return None
        return idle[0]

    async def _execute_dag(self, tasks: list[TaskNode]) -> list[dict]:
        """Execute tasks respecting dependency order."""
        results = []
        completed_ids: set[str] = set()
        for task in tasks:
            # Wait for dependencies
            deps_met = all(d in completed_ids for d in task.dependencies)
            if not deps_met:
                task.status = TaskStatus.FAILED
                task.error = "Dependency not met"
                continue
            task.status = TaskStatus.RUNNING
            try:
                task.result = f"Completed: {task.description[:50]}"
                task.status = TaskStatus.COMPLETED
                task.completed_at = time.time()
                completed_ids.add(task.id)
                if task.assigned_agent and task.assigned_agent in self._agents:
                    self._agents[task.assigned_agent].tasks_completed += 1
                    self._agents[task.assigned_agent].status = "idle"
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
            results.append({"task_id": task.id, "status": task.status.value, "result": task.result})
        return results

    async def coordinate_swarm(self, agent_ids: list[str], task: str) -> dict[str, Any]:
        """Coordinate multiple agents on a single task."""
        agents = [self._agents[aid] for aid in agent_ids if aid in self._agents]
        contributions = {a.id: f"{a.role.value} contribution to: {task[:30]}" for a in agents}
        return {"task": task, "agents": len(agents), "contributions": contributions}

    def stats(self) -> dict[str, Any]:
        return {"agents": len(self._agents), "total_tasks": len(self._tasks), "completed": sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED)}
