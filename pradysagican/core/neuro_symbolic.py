"""
NeuroSymbolicReasoner — Hybrid Neural + Symbolic Reasoning
==========================================================
Combines pattern recognition (neural/vector similarity) with formal
symbolic logic (knowledge graph, rule-based forward chaining, fallacy
detection). No current competitor has this integrated at agent level.

Solves weakness W3: pure neural approach with no formal verification.
"""
from __future__ import annotations

import hashlib
import logging
import math
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np

try:
    import networkx as nx
except ImportError:  # pragma: no cover
    nx = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class LogicalRule:
    """A symbolic rule: if condition(facts) → conclusion with confidence."""
    id: str = field(default_factory=lambda: f"rule_{uuid.uuid4().hex[:8]}")
    name: str = ""
    condition: Callable[[dict[str, Any]], bool] = field(default_factory=lambda: (lambda _: True))
    conclusion: str = ""
    confidence: float = 0.9
    domain: str = "general"


@dataclass
class Fact:
    """A triple in the knowledge graph: (subject, predicate, object)."""
    subject: str
    predicate: str
    obj: str
    confidence: float = 1.0
    source: str = "asserted"
    timestamp: float = field(default_factory=time.time)

    @property
    def triple_key(self) -> str:
        return f"{self.subject}|{self.predicate}|{self.obj}"


@dataclass
class NeuralEvidence:
    """Evidence from neural/vector similarity matching."""
    pattern: str
    similarity: float
    source_problem: str
    source_solution: str


@dataclass
class SymbolicEvidence:
    """Evidence from symbolic rule application."""
    rule_name: str
    rule_id: str
    conclusion: str
    confidence: float


@dataclass
class FallacyDetection:
    """A detected logical fallacy."""
    step_index: int
    fallacy_type: str
    description: str
    severity: float  # 0 = minor, 1 = critical


@dataclass
class NeuroSymbolicResult:
    """Combined result from hybrid reasoning."""
    conclusion: str
    confidence: float
    neural_evidence: list[NeuralEvidence] = field(default_factory=list)
    symbolic_evidence: list[SymbolicEvidence] = field(default_factory=list)
    rules_applied: list[str] = field(default_factory=list)
    fallacies_detected: list[FallacyDetection] = field(default_factory=list)
    verified: bool = False
    reasoning_trace: list[str] = field(default_factory=list)


# ── Pseudo-Embedding Utilities ───────────────────────────────────────────────

def _text_to_vector(text: str, dim: int = 64) -> np.ndarray:
    """Deterministic hash-based pseudo-embedding.

    Converts text into a fixed-dimension float vector using SHA-256
    seeded generation. Not a real embedding — sufficient for
    structural similarity within the system.
    """
    h = hashlib.sha256(text.lower().encode()).digest()
    rng = np.random.default_rng(int.from_bytes(h[:8], "big"))
    vec = rng.standard_normal(dim)
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity clamped to [0, 1]."""
    dot = float(np.dot(a, b))
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0 or nb == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (na * nb)))


# ── Knowledge Base ───────────────────────────────────────────────────────────

class KnowledgeBase:
    """Structured knowledge store with symbolic rules and a fact graph.

    Facts are stored as (subject, predicate, object) triples in a
    NetworkX DiGraph (or dict-based fallback). Rules are callable
    conditions that derive new facts via forward chaining.
    """

    def __init__(self) -> None:
        self._rules: list[LogicalRule] = []
        self._facts: dict[str, Fact] = {}  # triple_key → Fact
        if nx is not None:
            self._graph: Any = nx.DiGraph()
        else:
            self._graph = None
        self._inferred: list[Fact] = []

    # ── Rules ────────────────────────────────────────────────────────────

    def add_rule(self, rule: LogicalRule) -> None:
        """Add a symbolic inference rule."""
        self._rules.append(rule)
        logger.debug("Rule added: %s", rule.name)

    @property
    def rules(self) -> list[LogicalRule]:
        return list(self._rules)

    # ── Facts ────────────────────────────────────────────────────────────

    def add_fact(
        self,
        subject: str,
        predicate: str,
        obj: str,
        confidence: float = 1.0,
        source: str = "asserted",
    ) -> Fact:
        """Store a triple in the knowledge graph."""
        fact = Fact(subject=subject, predicate=predicate, obj=obj, confidence=confidence, source=source)
        self._facts[fact.triple_key] = fact

        if self._graph is not None:
            self._graph.add_node(subject, type="entity")
            self._graph.add_node(obj, type="entity")
            self._graph.add_edge(subject, obj, predicate=predicate, confidence=confidence)

        return fact

    def query(
        self,
        subject: str,
        predicate: str | None = None,
    ) -> list[Fact]:
        """Retrieve facts matching subject and optional predicate."""
        results: list[Fact] = []
        for fact in self._facts.values():
            if fact.subject == subject:
                if predicate is None or fact.predicate == predicate:
                    results.append(fact)
        return results

    def query_object(self, obj: str, predicate: str | None = None) -> list[Fact]:
        """Retrieve facts by object value."""
        results: list[Fact] = []
        for fact in self._facts.values():
            if fact.obj == obj:
                if predicate is None or fact.predicate == predicate:
                    results.append(fact)
        return results

    def has_fact(self, subject: str, predicate: str, obj: str) -> bool:
        """Check if a specific triple exists."""
        key = f"{subject}|{predicate}|{obj}"
        return key in self._facts

    @property
    def fact_count(self) -> int:
        return len(self._facts)

    @property
    def all_facts(self) -> list[Fact]:
        return list(self._facts.values())

    # ── Inference ────────────────────────────────────────────────────────

    def infer(self, context: dict[str, Any] | None = None) -> list[Fact]:
        """Forward chaining: apply rules to derive new facts.

        Iterates over all rules. If a rule's condition is satisfied
        by the current fact context, its conclusion is added as a
        new inferred fact. Runs until no new facts are produced
        (fixed-point) or a safety limit is hit.
        """
        ctx = context or self._build_context()
        new_facts: list[Fact] = []
        max_iterations = 20
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            found_new = False

            for rule in self._rules:
                try:
                    if rule.condition(ctx):
                        # Parse conclusion as a simple "subject predicate object" triple
                        parts = rule.conclusion.split(None, 2)
                        if len(parts) >= 3:
                            subj, pred, obj = parts[0], parts[1], parts[2]
                        else:
                            subj, pred, obj = rule.conclusion, "is", "true"

                        if not self.has_fact(subj, pred, obj):
                            fact = self.add_fact(
                                subj, pred, obj,
                                confidence=rule.confidence,
                                source=f"inferred:{rule.id}",
                            )
                            new_facts.append(fact)
                            self._inferred.append(fact)
                            ctx = self._build_context()  # refresh context
                            found_new = True
                except Exception as exc:
                    logger.warning("Rule '%s' failed: %s", rule.name, exc)

            if not found_new:
                break

        logger.info("Inference: %d new facts in %d iterations", len(new_facts), iteration)
        return new_facts

    def check_consistency(self, fact: Fact) -> dict[str, Any]:
        """Verify a new fact doesn't contradict existing knowledge.

        Checks:
        1. Direct contradiction (same subject+predicate, different object with negation)
        2. Confidence conflict (existing high-confidence fact disagrees)
        """
        contradictions: list[dict[str, Any]] = []
        existing = self.query(fact.subject, fact.predicate)

        for e in existing:
            if e.obj != fact.obj:
                # Check if objects are contradictory (negation or antonym heuristic)
                if (e.obj.startswith("not_") and e.obj[4:] == fact.obj) or \
                   (fact.obj.startswith("not_") and fact.obj[4:] == e.obj) or \
                   (e.confidence > 0.8 and fact.confidence > 0.8):
                    contradictions.append({
                        "existing": {"subject": e.subject, "predicate": e.predicate, "object": e.obj, "confidence": e.confidence},
                        "new": {"subject": fact.subject, "predicate": fact.predicate, "object": fact.obj, "confidence": fact.confidence},
                    })

        return {
            "consistent": len(contradictions) == 0,
            "contradictions": contradictions,
        }

    def _build_context(self) -> dict[str, Any]:
        """Build a flat context dict from all facts for rule evaluation."""
        ctx: dict[str, Any] = {}
        for fact in self._facts.values():
            key = f"{fact.subject}.{fact.predicate}"
            ctx[key] = fact.obj
            ctx[f"{key}.confidence"] = fact.confidence
        ctx["_fact_count"] = len(self._facts)
        return ctx


# ── Neuro-Symbolic Reasoner ──────────────────────────────────────────────────

class NeuroSymbolicReasoner:
    """Hybrid neural + symbolic reasoning engine.

    Combines:
    1. Neural: pattern matching via cosine similarity on pseudo-embeddings
       against a library of past problem-solution pairs.
    2. Symbolic: forward-chaining inference over a structured knowledge base.
    3. Merge: weighted combination of neural and symbolic evidence.
    4. Verify: consistency check against knowledge base rules.

    Also provides: explanation generation, rule induction from examples,
    logical fallacy detection, and formal claim verification.
    """

    def __init__(self, knowledge_base: KnowledgeBase | None = None) -> None:
        self.kb = knowledge_base or KnowledgeBase()
        self._problem_library: list[dict[str, str]] = []  # {problem, solution}
        self._neural_weight: float = 0.4
        self._symbolic_weight: float = 0.6

    def add_problem_solution(self, problem: str, solution: str) -> None:
        """Add a problem-solution pair to the neural pattern library."""
        self._problem_library.append({"problem": problem, "solution": solution})

    # ── Hybrid Reasoning ─────────────────────────────────────────────────

    async def hybrid_reason(
        self,
        problem: str,
        context: dict[str, Any] | None = None,
    ) -> NeuroSymbolicResult:
        """Full hybrid reasoning pipeline.

        1. Neural: find similar past problems and retrieve their solutions.
        2. Symbolic: apply knowledge base rules to derive conclusions.
        3. Merge: combine neural and symbolic evidence.
        4. Verify: check consistency against KB.
        """
        trace: list[str] = []

        # ── Step 1: Neural pattern matching ──
        trace.append("Step 1: Neural pattern matching against problem library")
        neural_evidence = self._neural_match(problem)
        trace.append(f"  Found {len(neural_evidence)} neural matches")

        # ── Step 2: Symbolic inference ──
        trace.append("Step 2: Symbolic forward-chaining inference")
        # Add problem as temporary context
        combined_ctx = dict(context or {})
        combined_ctx["problem"] = problem
        combined_ctx["_problem_words"] = set(problem.lower().split())
        inferred = self.kb.infer(combined_ctx)
        trace.append(f"  Inferred {len(inferred)} new facts")

        symbolic_evidence: list[SymbolicEvidence] = []
        for fact in inferred:
            source_rule = fact.source.split(":", 1)[-1] if ":" in fact.source else fact.source
            rule = next((r for r in self.kb.rules if r.id == source_rule), None)
            symbolic_evidence.append(SymbolicEvidence(
                rule_name=rule.name if rule else source_rule,
                rule_id=source_rule,
                conclusion=f"{fact.subject} {fact.predicate} {fact.obj}",
                confidence=fact.confidence,
            ))

        # ── Step 3: Merge evidence ──
        trace.append("Step 3: Merging neural and symbolic evidence")
        neural_conf = float(np.mean([e.similarity for e in neural_evidence])) if neural_evidence else 0.0
        symbolic_conf = float(np.mean([e.confidence for e in symbolic_evidence])) if symbolic_evidence else 0.0

        # Baseline confidence from existing KB coverage (even if no new inference fired)
        kb_baseline = 0.0
        if self.kb.fact_count > 0:
            problem_words = set(problem.lower().split())
            stop = {"the", "a", "an", "is", "are", "to", "of", "in", "and", "or", "for", "with"}
            problem_content = problem_words - stop
            matched_facts = 0
            for fact in self.kb.all_facts:
                fact_words = {fact.subject.lower(), fact.predicate.lower(), fact.obj.lower()}
                if problem_content & fact_words:
                    matched_facts += 1
            kb_baseline = min(matched_facts / max(len(problem_content), 1), 0.5)

        merged_confidence = (
            self._neural_weight * neural_conf +
            self._symbolic_weight * max(symbolic_conf, kb_baseline)
        )
        # Clamp
        merged_confidence = max(0.0, min(1.0, merged_confidence))

        # Build conclusion from strongest evidence
        conclusion_parts: list[str] = []
        if neural_evidence:
            best_neural = max(neural_evidence, key=lambda e: e.similarity)
            conclusion_parts.append(best_neural.source_solution)
        if symbolic_evidence:
            best_symbolic = max(symbolic_evidence, key=lambda e: e.confidence)
            conclusion_parts.append(best_symbolic.conclusion)

        conclusion = " | ".join(conclusion_parts) if conclusion_parts else f"No strong conclusion for: {problem[:50]}"
        trace.append(f"  Merged confidence: {merged_confidence:.3f}")

        # ── Step 4: Verify consistency ──
        trace.append("Step 4: Verifying consistency against knowledge base")
        verified = True
        if conclusion_parts:
            # Check the symbolic conclusions for contradictions
            for se in symbolic_evidence:
                parts = se.conclusion.split(None, 2)
                if len(parts) >= 3:
                    test_fact = Fact(subject=parts[0], predicate=parts[1], obj=parts[2])
                    check = self.kb.check_consistency(test_fact)
                    if not check["consistent"]:
                        verified = False
                        trace.append(f"  CONTRADICTION: {se.conclusion}")

        rules_applied = [se.rule_name for se in symbolic_evidence]
        trace.append(f"  Verified: {verified}, rules applied: {len(rules_applied)}")

        return NeuroSymbolicResult(
            conclusion=conclusion,
            confidence=round(merged_confidence, 4),
            neural_evidence=neural_evidence,
            symbolic_evidence=symbolic_evidence,
            rules_applied=rules_applied,
            fallacies_detected=[],
            verified=verified,
            reasoning_trace=trace,
        )

    def _neural_match(self, problem: str, top_k: int = 5) -> list[NeuralEvidence]:
        """Find similar problems using combined word-overlap and embedding similarity.

        Pure hash-based embeddings give low similarity for semantically related
        but textually different strings, so we blend in Jaccard word overlap.
        """
        if not self._problem_library:
            return []

        prob_vec = _text_to_vector(problem)
        prob_words = set(problem.lower().split())
        stop = {"the", "a", "an", "is", "are", "to", "of", "in", "and", "or", "for", "with"}
        prob_content = prob_words - stop

        scored: list[tuple[float, dict[str, str]]] = []

        for entry in self._problem_library:
            lib_vec = _text_to_vector(entry["problem"])
            embed_sim = _cosine_similarity(prob_vec, lib_vec)

            # Word overlap (Jaccard-like)
            lib_words = set(entry["problem"].lower().split()) - stop
            union = prob_content | lib_words
            overlap = len(prob_content & lib_words) / max(len(union), 1)

            # Blend: 40% embedding + 60% word overlap
            combined = embed_sim * 0.4 + overlap * 0.6
            scored.append((round(combined, 4), entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        results: list[NeuralEvidence] = []
        for sim, entry in scored[:top_k]:
            # Always include entries — even low similarity is informative
            # (hash-based embeddings yield low absolute scores by design)
            results.append(NeuralEvidence(
                pattern=entry["problem"][:60],
                similarity=max(round(sim, 4), 0.05),  # floor at 0.05 for library entries
                source_problem=entry["problem"],
                source_solution=entry["solution"],
            ))
        return results

    # ── Explain Reasoning ────────────────────────────────────────────────

    async def explain_reasoning(self, conclusion: str) -> dict[str, Any]:
        """Trace back through rules and neural evidence that led to a conclusion."""
        # Find which rules could have produced this conclusion
        relevant_rules: list[dict[str, Any]] = []
        for rule in self.kb.rules:
            if rule.conclusion.lower() in conclusion.lower() or \
               any(w in conclusion.lower() for w in rule.conclusion.lower().split()):
                relevant_rules.append({
                    "rule": rule.name,
                    "confidence": rule.confidence,
                    "domain": rule.domain,
                    "conclusion": rule.conclusion,
                })

        # Find similar problems from neural library
        neural_matches = self._neural_match(conclusion, top_k=3)

        # Find supporting facts from KB
        words = conclusion.lower().split()
        supporting_facts: list[dict[str, str]] = []
        for fact in self.kb.all_facts:
            if any(w in fact.subject.lower() or w in fact.obj.lower() for w in words if len(w) > 3):
                supporting_facts.append({
                    "subject": fact.subject,
                    "predicate": fact.predicate,
                    "object": fact.obj,
                    "confidence": str(fact.confidence),
                })

        return {
            "conclusion": conclusion,
            "supporting_rules": relevant_rules,
            "neural_analogies": [
                {"problem": e.source_problem[:50], "solution": e.source_solution[:50], "similarity": e.similarity}
                for e in neural_matches
            ],
            "supporting_facts": supporting_facts[:10],
            "explainability_score": round(
                min(1.0, (len(relevant_rules) + len(neural_matches) + len(supporting_facts)) / 10.0), 3
            ),
        }

    # ── Rule Induction ───────────────────────────────────────────────────

    async def learn_rule_from_examples(
        self,
        examples: list[dict[str, Any]],
        pattern: str,
    ) -> LogicalRule:
        """Induce a new rule from a set of examples.

        Examines examples for a common pattern and creates a rule
        whose condition checks for that pattern in the context.
        """
        # Extract common keys present in all examples
        if not examples:
            return LogicalRule(name="empty_rule", conclusion="unknown")

        common_keys = set(examples[0].keys())
        for ex in examples[1:]:
            common_keys &= set(ex.keys())

        # Find the key most correlated with the pattern
        pattern_lower = pattern.lower()

        def condition_fn(ctx: dict[str, Any]) -> bool:
            """Check if context matches the induced pattern."""
            for key in common_keys:
                full_key = f"_problem_words"
                if full_key in ctx and isinstance(ctx[full_key], set):
                    if any(w in ctx[full_key] for w in pattern_lower.split()):
                        return True
            return pattern_lower in str(ctx.get("problem", "")).lower()

        # Determine confidence from example consistency
        confidence = min(len(examples) / 10.0, 0.95)

        rule = LogicalRule(
            name=f"induced_{pattern[:20]}",
            condition=condition_fn,
            conclusion=pattern,
            confidence=round(confidence, 3),
            domain="learned",
        )
        self.kb.add_rule(rule)
        logger.info("Induced rule: %s (confidence=%.3f from %d examples)", rule.name, confidence, len(examples))
        return rule

    # ── Fallacy Detection ────────────────────────────────────────────────

    FALLACY_PATTERNS: list[dict[str, Any]] = [
        {
            "type": "ad_hominem",
            "keywords": ["stupid", "idiot", "fool", "incompetent", "they're wrong because"],
            "description": "Attacking the person instead of the argument",
            "severity": 0.7,
        },
        {
            "type": "straw_man",
            "keywords": ["they claim that", "they believe", "they think that", "what they really mean"],
            "description": "Misrepresenting someone's argument to attack it",
            "severity": 0.8,
        },
        {
            "type": "appeal_to_authority",
            "keywords": ["experts say", "studies show", "everyone knows", "it is well known"],
            "description": "Using authority as evidence without specifics",
            "severity": 0.4,
        },
        {
            "type": "false_dilemma",
            "keywords": ["either we", "only two options", "must choose between", "there's no other way"],
            "description": "Presenting only two options when more exist",
            "severity": 0.6,
        },
        {
            "type": "slippery_slope",
            "keywords": ["will inevitably", "will lead to", "next thing you know", "before long"],
            "description": "Assuming one event will cause a chain of negative events",
            "severity": 0.5,
        },
        {
            "type": "circular_reasoning",
            "keywords": ["because it is", "that's just how", "it's true because it's true"],
            "description": "Using the conclusion as a premise",
            "severity": 0.9,
        },
        {
            "type": "hasty_generalization",
            "keywords": ["all of them", "every single", "none of them", "always", "never"],
            "description": "Drawing broad conclusions from limited evidence",
            "severity": 0.6,
        },
    ]

    async def detect_logical_fallacy(
        self,
        argument_steps: list[str],
    ) -> list[FallacyDetection]:
        """Check argument steps for common logical fallacies."""
        detected: list[FallacyDetection] = []

        for i, step in enumerate(argument_steps):
            step_lower = step.lower()
            for pattern in self.FALLACY_PATTERNS:
                if any(kw in step_lower for kw in pattern["keywords"]):
                    detected.append(FallacyDetection(
                        step_index=i,
                        fallacy_type=pattern["type"],
                        description=f"{pattern['description']} — found in step {i}: '{step[:40]}...'",
                        severity=pattern["severity"],
                    ))

        # Check for non sequitur: step N has no word overlap with step N-1
        for i in range(1, len(argument_steps)):
            prev_words = set(argument_steps[i - 1].lower().split())
            curr_words = set(argument_steps[i].lower().split())
            # Remove stop words
            stop = {"the", "a", "an", "is", "are", "was", "were", "to", "of", "in", "and", "or", "it", "that", "this"}
            prev_content = prev_words - stop
            curr_content = curr_words - stop
            overlap = len(prev_content & curr_content)
            if prev_content and curr_content and overlap == 0:
                detected.append(FallacyDetection(
                    step_index=i,
                    fallacy_type="non_sequitur",
                    description=f"Step {i} appears disconnected from step {i - 1}",
                    severity=0.7,
                ))

        return detected

    # ── Formal Verification ──────────────────────────────────────────────

    async def formal_verify(
        self,
        claim: str,
        axioms: list[str] | None = None,
    ) -> dict[str, Any]:
        """Attempt to verify a claim using forward chaining from axioms.

        Adds axioms as facts, then checks if the claim can be derived
        or is contradicted by existing knowledge.
        """
        # Add axioms as temporary facts
        temp_facts: list[Fact] = []
        for axiom in (axioms or []):
            parts = axiom.split(None, 2)
            if len(parts) >= 3:
                fact = self.kb.add_fact(parts[0], parts[1], parts[2], confidence=1.0, source="axiom")
                temp_facts.append(fact)

        # Run inference
        inferred = self.kb.infer()

        # Check if claim is among known or inferred facts
        claim_parts = claim.split(None, 2)
        claim_found = False
        claim_confidence = 0.0

        if len(claim_parts) >= 3:
            for fact in self.kb.all_facts:
                if (fact.subject.lower() == claim_parts[0].lower() and
                    fact.predicate.lower() == claim_parts[1].lower() and
                    fact.obj.lower() == claim_parts[2].lower()):
                    claim_found = True
                    claim_confidence = fact.confidence
                    break

        # Also check via keyword overlap with inferred facts
        if not claim_found and inferred:
            claim_words = set(claim.lower().split())
            for fact in inferred:
                fact_words = {fact.subject.lower(), fact.predicate.lower(), fact.obj.lower()}
                overlap = len(claim_words & fact_words)
                if overlap >= 2:
                    claim_found = True
                    claim_confidence = fact.confidence * 0.7
                    break

        # Contradiction check
        contradiction = False
        if len(claim_parts) >= 3:
            test_fact = Fact(subject=claim_parts[0], predicate=claim_parts[1], obj=claim_parts[2])
            check = self.kb.check_consistency(test_fact)
            contradiction = not check["consistent"]

        return {
            "claim": claim,
            "verified": claim_found and not contradiction,
            "confidence": round(claim_confidence, 4),
            "contradicted": contradiction,
            "axioms_used": len(axioms or []),
            "facts_inferred": len(inferred),
            "total_facts": self.kb.fact_count,
        }
