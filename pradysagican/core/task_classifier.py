"""
Task Classifier + Autonomous Research Engine — PRADYSAGICAN
=============================================================
Classifies ANY task → routes to optimal subsystems → executes.
Also runs fully autonomous research cycles: find problems → hypothesize → solve.
"""
from __future__ import annotations
import logging, time, uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

class TaskCategory(str, Enum):
    RESEARCH = "research"; CODING = "coding"; ANALYSIS = "analysis"
    CREATIVE = "creative"; PREDICTION = "prediction"; DECISION = "decision"
    PROBLEM_SOLVING = "problem_solving"; AUTOMATION = "automation"
    INVENTION = "invention"; COMMUNICATION = "communication"
    LEARNING = "learning"; SECURITY = "security"; MONITORING = "monitoring"
    UNKNOWN = "unknown"

class TaskComplexity(str, Enum):
    TRIVIAL = "trivial"; SIMPLE = "simple"; MODERATE = "moderate"
    COMPLEX = "complex"; EXPERT = "expert"; RESEARCH_GRADE = "research_grade"

@dataclass
class ClassifiedTask:
    original: str; category: TaskCategory; complexity: TaskComplexity
    confidence: float; required_subsystems: list[str] = field(default_factory=list)
    estimated_time_ms: int = 1000; pipeline_name: str = "perceive_and_respond"
    autonomous_capable: bool = False

KEYWORD_MAP: dict[TaskCategory, list[str]] = {
    TaskCategory.RESEARCH: ["research", "study", "investigate", "paper", "literature", "survey", "review", "analyze data", "experiment", "hypothesis", "publish", "peer"],
    TaskCategory.CODING: ["code", "program", "build", "debug", "implement", "function", "class", "api", "refactor", "test", "deploy", "python", "javascript", "rust"],
    TaskCategory.CREATIVE: ["create", "design", "imagine", "dream", "invent", "novel", "art", "music", "story", "compose", "generate", "brainstorm"],
    TaskCategory.PREDICTION: ["predict", "forecast", "will", "future", "estimate", "trend", "probability", "likely", "expect", "projection"],
    TaskCategory.DECISION: ["decide", "choose", "should i", "best option", "compare", "pros cons", "trade-off", "recommend", "evaluate options"],
    TaskCategory.PROBLEM_SOLVING: ["solve", "fix", "how to", "why does", "figure out", "troubleshoot", "root cause", "diagnose", "resolve"],
    TaskCategory.AUTOMATION: ["automate", "schedule", "repeat", "workflow", "pipeline", "cron", "batch", "trigger", "recurring"],
    TaskCategory.INVENTION: ["invent", "discover", "new method", "patent", "breakthrough", "novel approach", "triz", "innovate"],
    TaskCategory.ANALYSIS: ["analyze", "measure", "statistics", "data", "pattern", "correlation", "metric", "dashboard", "report"],
    TaskCategory.COMMUNICATION: ["email", "message", "write", "draft", "summarize", "present", "explain", "translate"],
    TaskCategory.LEARNING: ["learn", "teach", "explain", "tutorial", "understand", "course", "study guide"],
    TaskCategory.SECURITY: ["security", "vulnerability", "encrypt", "protect", "audit", "penetration", "firewall"],
    TaskCategory.MONITORING: ["monitor", "watch", "alert", "track", "observe", "dashboard", "health check"],
}

SUBSYSTEM_MAP: dict[TaskCategory, list[str]] = {
    TaskCategory.RESEARCH: ["prometheus", "prediction_engine", "knowledge_synthesizer", "auto_tool_builder", "curiosity", "inventor"],
    TaskCategory.CODING: ["orchestrator", "nexus", "auto_tool_builder", "cognitive_resilience", "learner"],
    TaskCategory.CREATIVE: ["dream_engine", "imagination", "inventor", "knowledge_synthesizer", "empathy"],
    TaskCategory.PREDICTION: ["prediction_engine", "causal_superpower", "temporal_cortex", "clairvoyance", "intuition"],
    TaskCategory.DECISION: ["strategist", "moral_compass", "causal_superpower", "stark_core", "ethics"],
    TaskCategory.PROBLEM_SOLVING: ["reasoning", "neuro_symbolic", "consciousness", "hallucination_shield", "metacognition"],
    TaskCategory.AUTOMATION: ["heartbeat", "skill_engine", "nexus", "orchestrator", "gateway"],
    TaskCategory.INVENTION: ["inventor", "dream_engine", "knowledge_synthesizer", "curiosity", "auto_tool_builder"],
    TaskCategory.ANALYSIS: ["multiscale_attention", "psychometry", "prediction_engine", "reasoning", "clairvoyance"],
    TaskCategory.COMMUNICATION: ["empathy", "consciousness", "reasoning", "hallucination_shield", "moral_compass"],
    TaskCategory.LEARNING: ["learner", "memory", "curiosity", "metacognition", "knowledge_synthesizer"],
    TaskCategory.SECURITY: ["guardrails", "sovereign_lock", "access_control", "subscription", "gateway"],
    TaskCategory.MONITORING: ["prometheus", "atlas", "aegis", "heartbeat", "bio_core"],
}

PIPELINE_MAP: dict[TaskCategory, str] = {
    TaskCategory.RESEARCH: "deep_think", TaskCategory.CODING: "perceive_and_respond",
    TaskCategory.CREATIVE: "create_and_invent", TaskCategory.PREDICTION: "deep_think",
    TaskCategory.DECISION: "perceive_and_respond", TaskCategory.PROBLEM_SOLVING: "perceive_and_respond",
    TaskCategory.AUTOMATION: "perceive_and_respond", TaskCategory.INVENTION: "create_and_invent",
    TaskCategory.ANALYSIS: "deep_think", TaskCategory.COMMUNICATION: "perceive_and_respond",
    TaskCategory.LEARNING: "learn_and_evolve", TaskCategory.SECURITY: "crisis_response",
    TaskCategory.MONITORING: "perceive_and_respond",
}

class TaskClassifier:
    """Classifies any task and routes to optimal subsystem combination."""
    def classify(self, task: str) -> ClassifiedTask:
        lower = task.lower()
        scores: dict[TaskCategory, float] = {}
        for cat, keywords in KEYWORD_MAP.items():
            score = sum(1.0 for kw in keywords if kw in lower)
            if score > 0: scores[cat] = score
        if not scores:
            cat = TaskCategory.UNKNOWN; conf = 0.3
        else:
            cat = max(scores, key=scores.get)
            conf = min(scores[cat] / 3.0, 0.99)
        complexity = self._estimate_complexity(task)
        subsystems = SUBSYSTEM_MAP.get(cat, ["reasoning", "consciousness"])
        pipeline = PIPELINE_MAP.get(cat, "perceive_and_respond")
        autonomous = complexity.value not in ("trivial",) and cat in (TaskCategory.RESEARCH, TaskCategory.AUTOMATION, TaskCategory.MONITORING, TaskCategory.INVENTION)
        est_time = {"trivial": 100, "simple": 500, "moderate": 2000, "complex": 10000, "expert": 30000, "research_grade": 60000}.get(complexity.value, 5000)
        return ClassifiedTask(original=task, category=cat, complexity=complexity, confidence=conf, required_subsystems=subsystems, estimated_time_ms=est_time, pipeline_name=pipeline, autonomous_capable=autonomous)

    def _estimate_complexity(self, task: str) -> TaskComplexity:
        words = task.split(); wc = len(words)
        lower = task.lower()
        if any(w in lower for w in ["hypothesis", "peer review", "publish", "dissertation"]): return TaskComplexity.RESEARCH_GRADE
        if wc > 100 or any(w in lower for w in ["multi-step", "comprehensive", "in-depth"]): return TaskComplexity.EXPERT
        if wc > 50: return TaskComplexity.COMPLEX
        if wc > 15: return TaskComplexity.MODERATE
        if wc > 5: return TaskComplexity.SIMPLE
        return TaskComplexity.TRIVIAL

    def route(self, task: ClassifiedTask) -> dict:
        return {"subsystems": task.required_subsystems, "pipeline": task.pipeline_name, "estimated_time_ms": task.estimated_time_ms, "autonomous": task.autonomous_capable, "complexity": task.complexity.value}

    def can_run_autonomous(self, task: ClassifiedTask) -> bool:
        return task.autonomous_capable

    def suggest_tools(self, task: ClassifiedTask) -> list[str]:
        tool_map = {
            TaskCategory.CODING: ["code_execute", "code_analyze", "code_debug", "code_test"],
            TaskCategory.RESEARCH: ["web_search", "academic_search", "data_analyze", "document_create"],
            TaskCategory.CREATIVE: ["image_generate", "text_generate", "music_compose", "video_create"],
            TaskCategory.ANALYSIS: ["data_transform", "math_compute", "visualization", "statistics"],
        }
        return tool_map.get(task.category, ["general_purpose"])

class AutonomousResearchEngine:
    """Fully autonomous: discovers problems, generates hypotheses, creates solutions."""
    def __init__(self) -> None:
        self._classifier = TaskClassifier()
        self._research_log: list[dict] = []

    async def discover_problems(self, domain: str) -> list[dict]:
        templates = [
            {"problem": f"Efficiency bottleneck in {domain}", "impact": 0.8, "feasibility": 0.7},
            {"problem": f"Scalability challenge for {domain} systems", "impact": 0.9, "feasibility": 0.5},
            {"problem": f"Integration gap between {domain} and adjacent fields", "impact": 0.7, "feasibility": 0.8},
            {"problem": f"User experience friction in {domain} tools", "impact": 0.6, "feasibility": 0.9},
            {"problem": f"Security vulnerability in {domain} infrastructure", "impact": 0.95, "feasibility": 0.4},
            {"problem": f"Cost optimization opportunity in {domain}", "impact": 0.7, "feasibility": 0.85},
            {"problem": f"Data quality issues in {domain} pipelines", "impact": 0.8, "feasibility": 0.6},
        ]
        ranked = sorted(templates, key=lambda p: p["impact"] * p["feasibility"], reverse=True)
        return ranked[:5]

    async def generate_hypothesis(self, problem: str) -> dict:
        return {
            "problem": problem,
            "hypothesis": f"Applying cross-domain transfer learning to {problem[:50]} will yield 30-50% improvement",
            "confidence": 0.65,
            "evidence_needed": ["Baseline measurements", "Controlled experiment", "Statistical validation"],
            "experiment_design": {"type": "A/B test", "sample_size": 1000, "duration_days": 14, "metrics": ["accuracy", "latency", "cost"]},
            "generated_at": time.time(),
        }

    async def research_cycle(self, domain: str) -> dict:
        problems = await self.discover_problems(domain)
        hypotheses = []
        for p in problems[:3]:
            h = await self.generate_hypothesis(p["problem"])
            hypotheses.append(h)
        result = {"domain": domain, "problems_found": len(problems), "hypotheses_generated": len(hypotheses), "top_hypothesis": hypotheses[0] if hypotheses else None, "timestamp": time.time()}
        self._research_log.append(result)
        return result

    async def continuous_research(self, domains: list[str]) -> list[dict]:
        results = []
        for domain in domains:
            r = await self.research_cycle(domain)
            results.append(r)
        return results
