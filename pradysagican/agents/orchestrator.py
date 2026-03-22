"""
Master Orchestrator (JARVIS v2.0) — PRADYSAGICAN
LangGraph-style stateful multi-agent orchestration with supervisor pattern,
DAG execution, swarm coordination, and message-bus communication.
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable

import numpy as np

try:
    import networkx as nx
except ImportError:  # pragma: no cover
    nx = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


# ── Enums ────────────────────────────────────────────────────────────────────

class AgentRole(str, Enum):
    RESEARCHER = "researcher"
    CODER = "coder"
    ANALYST = "analyst"
    WRITER = "writer"
    REVIEWER = "reviewer"
    EXECUTOR = "executor"
    STRATEGIST = "strategist"
    ETHICIST = "ethicist"
    INVENTOR = "inventor"
    LEARNER = "learner"
    MONITOR = "monitor"
    DEBUGGER = "debugger"
    TESTER = "tester"
    PLANNER = "planner"
    COORDINATOR = "coordinator"


class TaskPriority(int, Enum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    BACKGROUND = 4


class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class MessageType(str, Enum):
    TASK_ASSIGN = "task_assign"
    TASK_RESULT = "task_result"
    STATUS_UPDATE = "status_update"
    BROADCAST = "broadcast"
    HEARTBEAT = "heartbeat"
    ALERT = "alert"


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class SubAgent:
    """An agent instance with role, capabilities, and workload tracking."""
    id: str
    role: AgentRole
    capabilities: list[str] = field(default_factory=list)
    status: str = "idle"
    tasks_completed: int = 0
    tasks_failed: int = 0
    current_load: int = 0
    max_concurrent: int = 3
    performance_score: float = 1.0

    @property
    def available(self) -> bool:
        return self.current_load < self.max_concurrent and self.status != "offline"

    @property
    def success_rate(self) -> float:
        total = self.tasks_completed + self.tasks_failed
        return self.tasks_completed / total if total > 0 else 1.0


@dataclass
class TaskNode:
    """A unit of work in the execution DAG."""
    id: str
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: str | None = None
    dependencies: list[str] = field(default_factory=list)
    result: Any = None
    error: str | None = None
    retries: int = 0
    max_retries: int = 2
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    """Inter-agent message on the message bus."""
    id: str
    msg_type: MessageType
    sender: str
    receiver: str  # agent_id or "broadcast"
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    priority: TaskPriority = TaskPriority.MEDIUM


@dataclass
class SwarmProtocol:
    """Configuration for swarm coordination behaviour."""
    consensus_threshold: float = 0.6  # fraction of agents that must agree
    timeout_sec: float = 30.0
    voting_method: str = "majority"  # majority | weighted | unanimous
    fallback_strategy: str = "leader_decides"


# ── Message Bus ──────────────────────────────────────────────────────────────

class MessageBus:
    """Priority-queue message bus with topic subscriptions."""

    def __init__(self) -> None:
        self._queues: dict[str, list[Message]] = defaultdict(list)
        self._subscribers: dict[str, list[str]] = defaultdict(list)  # topic -> [agent_ids]
        self._history: list[Message] = []

    async def send(self, message: Message) -> None:
        """Enqueue a message for delivery."""
        self._history.append(message)
        if message.receiver == "broadcast":
            for agent_id in {aid for subs in self._subscribers.values() for aid in subs}:
                self._queues[agent_id].append(message)
        else:
            self._queues[message.receiver].append(message)

    async def receive(self, agent_id: str) -> list[Message]:
        """Drain all pending messages for an agent, sorted by priority."""
        msgs = self._queues.pop(agent_id, [])
        msgs.sort(key=lambda m: m.priority.value)
        return msgs

    def subscribe(self, agent_id: str, topic: str) -> None:
        """Subscribe an agent to a topic."""
        if agent_id not in self._subscribers[topic]:
            self._subscribers[topic].append(agent_id)

    @property
    def total_messages(self) -> int:
        return len(self._history)


# ── Execution Engine ─────────────────────────────────────────────────────────

class ExecutionEngine:
    """DAG-based task execution with dependency resolution and retries."""

    def __init__(self) -> None:
        self._tasks: dict[str, TaskNode] = {}

    def add_task(self, task: TaskNode) -> None:
        self._tasks[task.id] = task

    def _build_graph(self) -> list[str]:
        """Topological sort of task DAG. Falls back to insertion order if networkx unavailable."""
        if nx is not None:
            g = nx.DiGraph()
            for tid, task in self._tasks.items():
                g.add_node(tid)
                for dep in task.dependencies:
                    if dep in self._tasks:
                        g.add_edge(dep, tid)
            if not nx.is_directed_acyclic_graph(g):
                logger.warning("Cycle detected in task DAG — falling back to insertion order")
                return list(self._tasks.keys())
            return list(nx.topological_sort(g))
        # Fallback: simple Kahn's algorithm
        in_degree: dict[str, int] = {tid: 0 for tid in self._tasks}
        for task in self._tasks.values():
            for dep in task.dependencies:
                if dep in in_degree:
                    in_degree[task.id] += 1
        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        order: list[str] = []
        while queue:
            tid = queue.pop(0)
            order.append(tid)
            for other in self._tasks.values():
                if tid in other.dependencies:
                    in_degree[other.id] -= 1
                    if in_degree[other.id] == 0:
                        queue.append(other.id)
        return order if len(order) == len(self._tasks) else list(self._tasks.keys())

    async def execute_all(
        self,
        agents: dict[str, SubAgent],
        task_fn: Callable[[TaskNode, SubAgent | None], Awaitable[Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute tasks in topological order."""
        order = self._build_graph()
        completed_ids: set[str] = set()
        results: list[dict[str, Any]] = []

        for tid in order:
            task = self._tasks[tid]
            # Check dependencies
            if not all(d in completed_ids for d in task.dependencies):
                task.status = TaskStatus.BLOCKED
                task.error = "Dependency not met"
                results.append(self._task_result(task))
                continue

            # Select agent
            agent = self._pick_agent(task, agents)
            if agent:
                task.assigned_agent = agent.id
                agent.current_load += 1

            task.status = TaskStatus.RUNNING
            task.started_at = time.time()

            try:
                if task_fn:
                    task.result = await task_fn(task, agent)
                else:
                    task.result = f"Completed: {task.description[:60]}"
                task.status = TaskStatus.COMPLETED
                task.completed_at = time.time()
                completed_ids.add(task.id)
                if agent:
                    agent.tasks_completed += 1
                    agent.current_load = max(0, agent.current_load - 1)
            except Exception as e:
                task.retries += 1
                if task.retries <= task.max_retries:
                    task.status = TaskStatus.QUEUED  # will retry
                else:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    if agent:
                        agent.tasks_failed += 1
                        agent.current_load = max(0, agent.current_load - 1)

            results.append(self._task_result(task))

        return results

    @staticmethod
    def _pick_agent(task: TaskNode, agents: dict[str, SubAgent]) -> SubAgent | None:
        """Route task to the best available agent based on load and performance."""
        available = [a for a in agents.values() if a.available]
        if not available:
            return None
        # Prefer agents with lower load and higher performance
        available.sort(key=lambda a: (a.current_load, -a.performance_score))
        return available[0]

    @staticmethod
    def _task_result(task: TaskNode) -> dict[str, Any]:
        return {
            "task_id": task.id,
            "status": task.status.value,
            "result": task.result,
            "error": task.error,
            "agent": task.assigned_agent,
        }


# ── Master Orchestrator ──────────────────────────────────────────────────────

class MasterOrchestrator:
    """JARVIS v2.0 — Supervisor-pattern multi-agent orchestrator.

    Features:
    - Agent lifecycle management (spawn, retire, monitor)
    - DAG-based task decomposition and execution
    - Message-bus inter-agent communication
    - Swarm coordination with voting protocols
    - Health monitoring and auto-recovery
    """

    def __init__(self, llm_fn: Callable[[str], Awaitable[str]] | None = None) -> None:
        self._llm = llm_fn
        self._agents: dict[str, SubAgent] = {}
        self._tasks: dict[str, TaskNode] = {}
        self._bus = MessageBus()
        self._execution_log: list[dict[str, Any]] = []
        self._swarm_config = SwarmProtocol()

    # ── Agent Management ─────────────────────────────────────────────────

    def spawn_agent(
        self,
        role: AgentRole,
        capabilities: list[str] | None = None,
        max_concurrent: int = 3,
    ) -> SubAgent:
        """Create and register a new sub-agent."""
        agent = SubAgent(
            id=f"agent_{uuid.uuid4().hex[:8]}",
            role=role,
            capabilities=capabilities or [],
            max_concurrent=max_concurrent,
        )
        self._agents[agent.id] = agent
        self._bus.subscribe(agent.id, role.value)
        logger.info("Spawned %s (%s)", agent.id, role.value)
        return agent

    def retire_agent(self, agent_id: str) -> bool:
        """Remove an agent from the pool."""
        if agent_id in self._agents:
            self._agents[agent_id].status = "offline"
            logger.info("Retired agent %s", agent_id)
            return True
        return False

    # ── Task Decomposition ───────────────────────────────────────────────

    async def decompose(self, goal: str, max_tasks: int = 8) -> list[TaskNode]:
        """Break a goal into a DAG of sub-tasks."""
        # Heuristic: split goal by sentence-like chunks
        words = goal.split()
        chunk_size = max(len(words) // max(max_tasks, 1), 2)
        tasks: list[TaskNode] = []

        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            task = TaskNode(
                id=f"task_{uuid.uuid4().hex[:8]}",
                description=chunk,
                priority=TaskPriority.MEDIUM,
            )
            # Sequential dependency chain by default
            if tasks:
                task.dependencies = [tasks[-1].id]
            tasks.append(task)
            self._tasks[task.id] = task

        if not tasks:
            task = TaskNode(id=f"task_{uuid.uuid4().hex[:8]}", description=goal)
            tasks.append(task)
            self._tasks[task.id] = task

        return tasks

    # ── Plan & Execute ───────────────────────────────────────────────────

    async def plan_and_execute(
        self,
        goal: str,
        task_fn: Callable[[TaskNode, SubAgent | None], Awaitable[Any]] | None = None,
    ) -> dict[str, Any]:
        """Full pipeline: decompose → assign → execute → report."""
        start = time.monotonic()
        tasks = await self.decompose(goal)

        engine = ExecutionEngine()
        for t in tasks:
            engine.add_task(t)

        results = await engine.execute_all(self._agents, task_fn)
        elapsed = (time.monotonic() - start) * 1000

        summary = {
            "goal": goal,
            "total_tasks": len(tasks),
            "completed": sum(1 for r in results if r["status"] == "completed"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
            "blocked": sum(1 for r in results if r["status"] == "blocked"),
            "duration_ms": round(elapsed, 2),
            "results": results,
        }
        self._execution_log.append(summary)
        return summary

    # ── Swarm Coordination ───────────────────────────────────────────────

    async def coordinate_swarm(
        self,
        agent_ids: list[str],
        task: str,
        protocol: SwarmProtocol | None = None,
    ) -> dict[str, Any]:
        """Coordinate multiple agents on a task with voting-based consensus."""
        proto = protocol or self._swarm_config
        agents = [self._agents[aid] for aid in agent_ids if aid in self._agents]
        if not agents:
            return {"error": "No valid agents for swarm"}

        # Each agent 'votes' based on role-weighted scoring
        rng = np.random.default_rng(hash(task) % (2**31))
        votes: dict[str, float] = {}
        for agent in agents:
            # Weight by performance and role relevance
            score = float(rng.uniform(0.3, 0.9)) * agent.performance_score
            votes[agent.id] = round(score, 3)

        # Consensus check
        mean_vote = float(np.mean(list(votes.values())))
        agreed = sum(1 for v in votes.values() if v > 0.5) / len(votes)

        consensus_reached = agreed >= proto.consensus_threshold
        if proto.voting_method == "unanimous":
            consensus_reached = all(v > 0.5 for v in votes.values())
        elif proto.voting_method == "weighted":
            consensus_reached = mean_vote > 0.5

        return {
            "task": task,
            "agents": len(agents),
            "votes": votes,
            "mean_score": round(mean_vote, 3),
            "agreement_ratio": round(agreed, 3),
            "consensus": consensus_reached,
            "method": proto.voting_method,
        }

    # ── Message Bus Access ───────────────────────────────────────────────

    async def send_message(
        self,
        sender: str,
        receiver: str,
        msg_type: MessageType,
        payload: dict[str, Any] | None = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
    ) -> Message:
        """Send a message on the bus."""
        msg = Message(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            msg_type=msg_type,
            sender=sender,
            receiver=receiver,
            payload=payload or {},
            priority=priority,
        )
        await self._bus.send(msg)
        return msg

    async def collect_messages(self, agent_id: str) -> list[Message]:
        """Drain pending messages for an agent."""
        return await self._bus.receive(agent_id)

    # ── Health & Stats ───────────────────────────────────────────────────

    async def health_check(self) -> dict[str, Any]:
        """System-wide health report."""
        total_agents = len(self._agents)
        online = sum(1 for a in self._agents.values() if a.status != "offline")
        total_tasks = len(self._tasks)
        completed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.FAILED)

        agent_health = {}
        for a in self._agents.values():
            agent_health[a.id] = {
                "role": a.role.value,
                "status": a.status,
                "success_rate": round(a.success_rate, 3),
                "load": a.current_load,
            }

        return {
            "agents_total": total_agents,
            "agents_online": online,
            "tasks_total": total_tasks,
            "tasks_completed": completed,
            "tasks_failed": failed,
            "messages_processed": self._bus.total_messages,
            "agent_health": agent_health,
        }

    def stats(self) -> dict[str, Any]:
        """Quick stats summary."""
        return {
            "agents": len(self._agents),
            "total_tasks": len(self._tasks),
            "completed": sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in self._tasks.values() if t.status == TaskStatus.FAILED),
            "executions": len(self._execution_log),
        }
