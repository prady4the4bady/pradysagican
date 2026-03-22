"""
Invention Engine v2.0 — PRADYSAGICAN
Autonomous discovery using all 40 TRIZ principles, research pipelines,
innovation matrices, patent analysis, and AI Scientist methodology (Sakana AI).
"""
from __future__ import annotations

import logging
import random
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


# ── All 40 TRIZ Inventive Principles ────────────────────────────────────────

TRIZ_PRINCIPLES: list[dict[str, str]] = [
    {"id": "01", "name": "Segmentation", "desc": "Divide an object into independent parts"},
    {"id": "02", "name": "Taking out", "desc": "Separate an interfering part or property"},
    {"id": "03", "name": "Local quality", "desc": "Change uniform structure to non-uniform"},
    {"id": "04", "name": "Asymmetry", "desc": "Change symmetric form to asymmetric"},
    {"id": "05", "name": "Merging", "desc": "Combine identical or similar objects/operations"},
    {"id": "06", "name": "Universality", "desc": "Make a part perform multiple functions"},
    {"id": "07", "name": "Nested doll", "desc": "Place one object inside another"},
    {"id": "08", "name": "Anti-weight", "desc": "Compensate weight with another force"},
    {"id": "09", "name": "Preliminary anti-action", "desc": "Pre-stress to counter known harmful effects"},
    {"id": "10", "name": "Preliminary action", "desc": "Perform required changes in advance"},
    {"id": "11", "name": "Beforehand cushioning", "desc": "Prepare emergency means in advance"},
    {"id": "12", "name": "Equipotentiality", "desc": "Change conditions to eliminate lifting/lowering"},
    {"id": "13", "name": "The other way round", "desc": "Invert the action"},
    {"id": "14", "name": "Spheroidality-Curvature", "desc": "Move from flat to curved surfaces"},
    {"id": "15", "name": "Dynamics", "desc": "Allow characteristics to change optimally"},
    {"id": "16", "name": "Partial or excessive actions", "desc": "Do slightly less or more than required"},
    {"id": "17", "name": "Another dimension", "desc": "Move to multi-dimensional space"},
    {"id": "18", "name": "Mechanical vibration", "desc": "Use oscillation or resonance"},
    {"id": "19", "name": "Periodic action", "desc": "Replace continuous with periodic action"},
    {"id": "20", "name": "Continuity of useful action", "desc": "Carry on work without pauses"},
    {"id": "21", "name": "Skipping", "desc": "Conduct a process at high speed"},
    {"id": "22", "name": "Blessing in disguise", "desc": "Use harmful factors to achieve positive effect"},
    {"id": "23", "name": "Feedback", "desc": "Introduce or improve feedback"},
    {"id": "24", "name": "Intermediary", "desc": "Use an intermediate carrier or process"},
    {"id": "25", "name": "Self-service", "desc": "Make an object serve and repair itself"},
    {"id": "26", "name": "Copying", "desc": "Use simpler/cheaper copies instead of originals"},
    {"id": "27", "name": "Cheap short-living objects", "desc": "Replace expensive durability with cheap disposability"},
    {"id": "28", "name": "Mechanics substitution", "desc": "Replace mechanical means with sensory"},
    {"id": "29", "name": "Pneumatics and hydraulics", "desc": "Use gas or liquid parts of an object"},
    {"id": "30", "name": "Flexible shells and thin films", "desc": "Use flexible shells and thin films"},
    {"id": "31", "name": "Porous materials", "desc": "Make an object porous or add porous elements"},
    {"id": "32", "name": "Colour changes", "desc": "Change colour or transparency"},
    {"id": "33", "name": "Homogeneity", "desc": "Objects interacting should be of same material"},
    {"id": "34", "name": "Discarding and recovering", "desc": "Discard or modify parts that have fulfilled function"},
    {"id": "35", "name": "Parameter changes", "desc": "Change physical state, concentration, flexibility"},
    {"id": "36", "name": "Phase transitions", "desc": "Use phenomena during phase transitions"},
    {"id": "37", "name": "Thermal expansion", "desc": "Use thermal expansion/contraction of materials"},
    {"id": "38", "name": "Strong oxidants", "desc": "Replace common air with oxygen-enriched"},
    {"id": "39", "name": "Inert atmosphere", "desc": "Replace normal environment with inert one"},
    {"id": "40", "name": "Composite materials", "desc": "Change from uniform to composite materials"},
]

TRIZ_PRINCIPLE_NAMES = [p["name"] for p in TRIZ_PRINCIPLES]


# ── TRIZ Contradiction Matrix (simplified) ──────────────────────────────────

CONTRADICTION_PARAMS = [
    "speed", "force", "stress", "stability", "reliability",
    "complexity", "ease_of_operation", "adaptability", "productivity", "accuracy",
]


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class Hypothesis:
    """A testable hypothesis with evidence tracking."""
    id: str
    description: str
    confidence: float = 0.3
    evidence_for: list[str] = field(default_factory=list)
    evidence_against: list[str] = field(default_factory=list)
    triz_principle: str | None = None
    status: str = "active"  # active | confirmed | refuted


@dataclass
class Invention:
    """A novel invention or solution."""
    id: str
    name: str
    problem_solved: str
    method: str
    novelty_score: float
    feasibility_score: float
    impact_score: float = 0.5
    triz_principles_used: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ResearchPaper:
    """Simulated research paper (AI Scientist pattern)."""
    title: str
    abstract: str
    hypothesis: str
    method: str
    results: dict[str, Any] = field(default_factory=dict)
    conclusion: str = ""
    novelty_score: float = 0.0


@dataclass
class PatentClaim:
    """A patent claim derived from an invention."""
    claim_number: int
    text: str
    dependent_on: list[int] = field(default_factory=list)
    novelty: float = 0.0
    breadth: float = 0.5  # 0 = very narrow, 1 = very broad


# ── Innovation Matrix ────────────────────────────────────────────────────────

class InnovationMatrix:
    """TRIZ contradiction matrix for suggesting inventive principles.

    Given an improving parameter and a worsening parameter, suggests
    which TRIZ principles are most likely to resolve the contradiction.
    """

    def __init__(self) -> None:
        self._rng = np.random.default_rng(42)
        # Pre-computed matrix: param_pair -> suggested principle indices
        self._matrix: dict[tuple[str, str], list[int]] = {}
        self._build_matrix()

    def _build_matrix(self) -> None:
        """Build a simplified contradiction matrix."""
        for i, p1 in enumerate(CONTRADICTION_PARAMS):
            for j, p2 in enumerate(CONTRADICTION_PARAMS):
                if i != j:
                    # Deterministic principle selection based on param indices
                    seed = (i * 17 + j * 31) % 40
                    indices = [(seed + k * 7) % 40 for k in range(4)]
                    self._matrix[(p1, p2)] = sorted(set(indices))

    async def suggest_principles(
        self,
        improving: str,
        worsening: str,
    ) -> list[dict[str, str]]:
        """Suggest TRIZ principles to resolve a technical contradiction."""
        key = (improving.lower(), worsening.lower())
        indices = self._matrix.get(key, [0, 4, 12, 24])
        return [TRIZ_PRINCIPLES[i] for i in indices if i < len(TRIZ_PRINCIPLES)]

    async def find_contradictions(
        self,
        problem: str,
    ) -> list[dict[str, Any]]:
        """Identify potential contradictions in a problem description."""
        lower = problem.lower()
        found: list[dict[str, Any]] = []

        for param in CONTRADICTION_PARAMS:
            if param.replace("_", " ") in lower or param in lower:
                # Find opposing parameters
                for other in CONTRADICTION_PARAMS:
                    if other != param and (other.replace("_", " ") in lower or other in lower):
                        principles = await self.suggest_principles(param, other)
                        found.append({
                            "improving": param,
                            "worsening": other,
                            "suggested_principles": [p["name"] for p in principles],
                        })
        if not found:
            # Default contradiction
            found.append({
                "improving": "productivity",
                "worsening": "complexity",
                "suggested_principles": ["Segmentation", "Universality", "Dynamics", "Self-service"],
            })
        return found


# ── Research Pipeline ────────────────────────────────────────────────────────

class ResearchPipeline:
    """AI Scientist-style automated research pipeline.

    Steps: identify problem → hypothesize → design experiment → run → analyse → publish.
    """

    def __init__(self) -> None:
        self._papers: list[ResearchPaper] = []

    async def run_study(
        self,
        problem: str,
        hypothesis: str,
        n_samples: int = 100,
    ) -> ResearchPaper:
        """Run a complete research study."""
        rng = np.random.default_rng(hash(problem) % (2**31))

        # Simulated experimental results
        control = rng.normal(loc=0.5, scale=0.15, size=n_samples)
        treatment = rng.normal(loc=0.5 + rng.uniform(0, 0.3), scale=0.15, size=n_samples)

        effect_size = float(np.mean(treatment) - np.mean(control))
        pooled_std = float(np.sqrt((np.var(control) + np.var(treatment)) / 2))
        cohens_d = effect_size / pooled_std if pooled_std > 0 else 0.0

        significant = abs(cohens_d) > 0.2

        results = {
            "control_mean": round(float(np.mean(control)), 4),
            "treatment_mean": round(float(np.mean(treatment)), 4),
            "effect_size": round(effect_size, 4),
            "cohens_d": round(cohens_d, 4),
            "significant": significant,
            "n_samples": n_samples,
        }

        paper = ResearchPaper(
            title=f"Investigating: {problem[:50]}",
            abstract=f"We test whether {hypothesis[:60]}. N={n_samples}, Cohen's d={cohens_d:.2f}.",
            hypothesis=hypothesis,
            method=f"Randomised controlled trial with {n_samples} samples per group",
            results=results,
            conclusion="Hypothesis supported" if significant else "Insufficient evidence",
            novelty_score=round(min(abs(cohens_d), 1.0), 3),
        )
        self._papers.append(paper)
        return paper

    @property
    def papers(self) -> list[ResearchPaper]:
        return list(self._papers)


# ── Patent Analyser ──────────────────────────────────────────────────────────

class PatentAnalyser:
    """Generate and analyse patent claims from inventions."""

    async def generate_claims(self, invention: Invention) -> list[PatentClaim]:
        """Generate patent claims for an invention."""
        claims: list[PatentClaim] = []

        # Independent claim
        claims.append(PatentClaim(
            claim_number=1,
            text=f"A method for {invention.problem_solved}, comprising {invention.method}",
            novelty=invention.novelty_score,
            breadth=0.8,
        ))

        # Dependent claims based on TRIZ principles used
        for i, principle in enumerate(invention.triz_principles_used[:3], start=2):
            claims.append(PatentClaim(
                claim_number=i,
                text=f"The method of claim 1, further comprising applying {principle} principle",
                dependent_on=[1],
                novelty=round(invention.novelty_score * 0.8, 3),
                breadth=0.5,
            ))

        return claims

    async def novelty_search(
        self,
        invention: Invention,
        prior_art: list[str],
    ) -> dict[str, Any]:
        """Check novelty against prior art (keyword overlap analysis)."""
        inv_words = set(invention.name.lower().split() + invention.method.lower().split())
        overlaps: list[dict[str, Any]] = []

        for art in prior_art:
            art_words = set(art.lower().split())
            overlap = len(inv_words & art_words)
            similarity = overlap / max(len(inv_words | art_words), 1)
            overlaps.append({"prior_art": art[:50], "similarity": round(similarity, 3)})

        max_sim = max((o["similarity"] for o in overlaps), default=0.0)
        novel = max_sim < 0.5

        return {
            "invention": invention.name,
            "novel": novel,
            "max_similarity": round(max_sim, 3),
            "prior_art_matches": overlaps,
            "recommendation": "Patentable" if novel else "Too similar to prior art",
        }


# ── Invention Engine ─────────────────────────────────────────────────────────

class InventionEngine:
    """Invention Engine v2.0 — Autonomous discovery and innovation.

    Features:
    - Problem identification via domain analysis
    - Hypothesis generation using all 40 TRIZ principles
    - TRIZ contradiction matrix for principle selection
    - Automated research pipeline (AI Scientist)
    - Patent claim generation and novelty analysis
    - Concept combination using merging/universality principles
    """

    def __init__(self) -> None:
        self._inventions: list[Invention] = []
        self._hypotheses: list[Hypothesis] = []
        self.matrix = InnovationMatrix()
        self.research = ResearchPipeline()
        self.patents = PatentAnalyser()

    # ── Problem Identification ───────────────────────────────────────────

    async def identify_problems(self, domain: str) -> list[dict[str, Any]]:
        """Systematic problem identification in a domain."""
        problem_types = [
            ("efficiency", f"Efficiency bottleneck in {domain}", 0.8),
            ("scalability", f"Scalability challenge for {domain}", 0.7),
            ("integration", f"Integration gap between {domain} and adjacent systems", 0.6),
            ("usability", f"User experience friction in {domain}", 0.7),
            ("cost", f"Cost optimisation opportunity in {domain}", 0.5),
            ("reliability", f"Reliability concern in {domain} under stress", 0.6),
            ("security", f"Security vulnerability surface in {domain}", 0.8),
        ]
        return [
            {"type": t, "problem": p, "severity": s}
            for t, p, s in problem_types
        ]

    # ── Hypothesis Generation ────────────────────────────────────────────

    async def generate_hypotheses(
        self,
        problem: str,
        n: int = 3,
    ) -> list[Hypothesis]:
        """Generate hypotheses using TRIZ-inspired approaches."""
        rng = random.Random(hash(problem))
        hypotheses: list[Hypothesis] = []

        selected = rng.sample(TRIZ_PRINCIPLES, min(n, len(TRIZ_PRINCIPLES)))
        for principle in selected:
            h = Hypothesis(
                id=f"hyp_{uuid.uuid4().hex[:8]}",
                description=f"Apply '{principle['name']}' ({principle['desc']}) to solve: {problem[:50]}",
                confidence=round(rng.uniform(0.2, 0.6), 3),
                triz_principle=principle["name"],
            )
            hypotheses.append(h)

        self._hypotheses.extend(hypotheses)
        return hypotheses

    async def evaluate_hypothesis(
        self,
        hypothesis: Hypothesis,
        test_results: dict[str, Any],
    ) -> Hypothesis:
        """Update hypothesis confidence based on test evidence."""
        if test_results.get("success", False):
            hypothesis.evidence_for.append(str(test_results)[:100])
            hypothesis.confidence = min(hypothesis.confidence + 0.15, 0.95)
            if hypothesis.confidence > 0.8:
                hypothesis.status = "confirmed"
        else:
            hypothesis.evidence_against.append(str(test_results)[:100])
            hypothesis.confidence = max(hypothesis.confidence - 0.1, 0.05)
            if hypothesis.confidence < 0.15:
                hypothesis.status = "refuted"
        return hypothesis

    # ── Concept Combination ──────────────────────────────────────────────

    async def combine_concepts(self, concepts: list[str]) -> Invention:
        """Create novel combinations using TRIZ Merging + Universality principles."""
        rng = random.Random(hash(tuple(concepts)))
        principles_used = rng.sample(TRIZ_PRINCIPLE_NAMES, min(3, len(TRIZ_PRINCIPLE_NAMES)))

        # Novelty: more diverse concepts → higher novelty
        unique_words = set()
        for c in concepts:
            unique_words.update(c.lower().split())
        novelty = min(len(unique_words) / 15.0, 0.95)

        # Feasibility: fewer concepts → more feasible
        feasibility = max(1.0 - len(concepts) * 0.15, 0.2)

        invention = Invention(
            id=f"inv_{uuid.uuid4().hex[:8]}",
            name=f"Novel_{concepts[0][:12]}_{concepts[-1][:12]}",
            problem_solved=f"Synergy of {len(concepts)} concepts",
            method=f"TRIZ-inspired merging using {', '.join(principles_used[:2])}",
            novelty_score=round(novelty, 3),
            feasibility_score=round(feasibility, 3),
            impact_score=round((novelty + feasibility) / 2, 3),
            triz_principles_used=principles_used,
        )
        self._inventions.append(invention)
        return invention

    # ── Full Innovation Cycle ────────────────────────────────────────────

    async def innovate(
        self,
        domain: str,
        problem: str | None = None,
    ) -> dict[str, Any]:
        """Run the full innovation pipeline: problem → hypothesis → research → invention."""
        # 1. Problem identification
        if problem is None:
            problems = await self.identify_problems(domain)
            problem = problems[0]["problem"] if problems else f"General challenge in {domain}"

        # 2. Find contradictions
        contradictions = await self.matrix.find_contradictions(problem)

        # 3. Generate hypotheses
        hypotheses = await self.generate_hypotheses(problem)

        # 4. Run research on top hypothesis
        if hypotheses:
            paper = await self.research.run_study(problem, hypotheses[0].description)
        else:
            paper = None

        # 5. Combine domain concepts into invention
        domain_words = [w for w in domain.split() if len(w) > 3]
        if problem:
            domain_words.extend(w for w in problem.split() if len(w) > 3)
        invention = await self.combine_concepts(domain_words[:5] or [domain])

        return {
            "domain": domain,
            "problem": problem,
            "contradictions": contradictions,
            "hypotheses": len(hypotheses),
            "research_result": paper.results if paper else None,
            "invention": {
                "name": invention.name,
                "novelty": invention.novelty_score,
                "feasibility": invention.feasibility_score,
                "triz_principles": invention.triz_principles_used,
            },
        }

    @property
    def inventions(self) -> list[Invention]:
        return list(self._inventions)

    @property
    def hypotheses(self) -> list[Hypothesis]:
        return list(self._hypotheses)
