"""Ingestion and routing layer for the 70 GPT helper bots catalog."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class GPTBotDefinition:
    """Normalized bot definition."""

    bot_id: int
    name: str
    category: str
    purpose: str
    notes: str
    tools_integrations: List[Dict[str, str]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.bot_id,
            "name": self.name,
            "category": self.category,
            "purpose": self.purpose,
            "notes": self.notes,
            "tools_integrations": self.tools_integrations,
        }


class GPTBotCatalog:
    """Catalog loader + lightweight semantic router for helper bots."""

    _CATEGORY_ARCHETYPES: Dict[str, Dict[str, Any]] = {
        "Social Media": {
            "archetype": "creator",
            "pipeline": ["audience-analysis", "hook-generation", "platform-adaptation", "engagement-pass"],
            "internal_systems": ["ORACLE", "MNEMOSYNE", "MORPHEUS"],
        },
        "Content Creation": {
            "archetype": "creator",
            "pipeline": ["brief-extraction", "outline", "drafting", "quality-rewrite"],
            "internal_systems": ["MNEMOSYNE", "SOCRATES", "LOGOS"],
        },
        "Business": {
            "archetype": "analyst",
            "pipeline": ["objective-decomposition", "market-evaluation", "strategy-synthesis", "risk-check"],
            "internal_systems": ["ATLAS", "SOCRATES", "ORACLE"],
        },
        "Productivity & Management": {
            "archetype": "strategist",
            "pipeline": ["task-triage", "constraint-mapping", "schedule-optimization", "execution-brief"],
            "internal_systems": ["CHRONOS", "PROMETHEUS", "MIDAS"],
        },
        "Creative Tools": {
            "archetype": "creator",
            "pipeline": ["style-selection", "creative-generation", "composition", "refinement"],
            "internal_systems": ["MORPHEUS", "MNEMOSYNE", "SOCRATES"],
        },
        "Personal Development": {
            "archetype": "mentor",
            "pipeline": ["goal-clarification", "self-assessment", "plan", "accountability-loop"],
            "internal_systems": ["PSYCHE", "ORACLE", "SOCRATES"],
        },
        "Strategy & Analysis": {
            "archetype": "analyst",
            "pipeline": ["problem-framing", "diagnostics", "option-ranking", "recommendation"],
            "internal_systems": ["ATLAS", "LOGOS", "SOCRATES"],
        },
        "E-commerce": {
            "archetype": "growth-operator",
            "pipeline": ["store-audit", "segment-analysis", "offer-optimization", "conversion-playbook"],
            "internal_systems": ["MIDAS", "ATLAS", "ORACLE"],
        },
        "Finance & Operations": {
            "archetype": "operator",
            "pipeline": ["input-validation", "workflow-automation", "compliance-pass", "reporting"],
            "internal_systems": ["FORTRESS", "MIDAS", "LOGOS"],
        },
        "Assistants": {
            "archetype": "assistant",
            "pipeline": ["intent-capture", "task-execution", "handoff-summary"],
            "internal_systems": ["MNEMOSYNE", "CHRONOS", "ORACLE"],
        },
        "Jobseekers": {
            "archetype": "coach",
            "pipeline": ["profile-assessment", "skill-gap-analysis", "practice-loop", "final-polish"],
            "internal_systems": ["SOCRATES", "ORACLE", "PSYCHE"],
        },
        "Customer Support": {
            "archetype": "support",
            "pipeline": ["issue-classification", "resolution-planning", "response-drafting", "csat-optimization"],
            "internal_systems": ["FORTRESS", "LOGOS", "ORACLE"],
        },
        "Marketing": {
            "archetype": "growth-marketer",
            "pipeline": ["goal-alignment", "message-design", "channel-optimization", "performance-loop"],
            "internal_systems": ["MIDAS", "ORACLE", "MNEMOSYNE"],
        },
        "Sales and Communication": {
            "archetype": "sales-strategist",
            "pipeline": ["buyer-persona", "objection-modeling", "pitch-scripting", "followup-plan"],
            "internal_systems": ["ORACLE", "SOCRATES", "MIDAS"],
        },
        "Writing": {
            "archetype": "writer",
            "pipeline": ["brief", "creative-pass", "coherence-pass", "final-edit"],
            "internal_systems": ["MORPHEUS", "LOGOS", "MNEMOSYNE"],
        },
    }

    def __init__(self, catalog_path: str | Path | None = None):
        self.catalog_path = (
            Path(catalog_path)
            if catalog_path is not None
            else Path(__file__).with_name("gpt_bots_catalog.json")
        )
        self._bots: List[GPTBotDefinition] = self._load_catalog()

    def _load_catalog(self) -> List[GPTBotDefinition]:
        candidate_paths = [
            self.catalog_path,
            Path("data/gpt_bots_catalog.json"),
        ]
        catalog_file: Optional[Path] = None
        for path in candidate_paths:
            if path.exists():
                catalog_file = path
                break
        if catalog_file is None:
            raise FileNotFoundError(
                f"Bot catalog not found in any candidate path: {[str(p) for p in candidate_paths]}"
            )

        payload = json.loads(catalog_file.read_text(encoding="utf-8"))
        bots: List[GPTBotDefinition] = []

        for raw in payload:
            bot = GPTBotDefinition(
                bot_id=int(raw["id"]),
                name=str(raw["name"]).strip(),
                category=str(raw["category"]).strip(),
                purpose=str(raw["purpose"]).strip(),
                notes=str(raw.get("notes") or "").strip(),
                tools_integrations=list(raw.get("tools_integrations") or []),
            )
            bots.append(bot)

        if not bots:
            raise ValueError("Bot catalog is empty")

        return bots

    def list_bots(self, category: Optional[str] = None, limit: int = 100) -> List[GPTBotDefinition]:
        filtered = self._bots
        if category:
            category_norm = category.strip().lower()
            filtered = [b for b in self._bots if b.category.lower() == category_norm]
        safe_limit = max(1, min(limit, 500))
        return filtered[:safe_limit]

    def list_categories(self) -> List[str]:
        return sorted({b.category for b in self._bots})

    def get_bot(self, identifier: str) -> Optional[GPTBotDefinition]:
        key = identifier.strip().lower()
        for bot in self._bots:
            if str(bot.bot_id) == key or bot.name.lower() == key:
                return bot
        return None

    def route(
        self,
        query: str,
        preferred_bot: Optional[str] = None,
        preferred_category: Optional[str] = None,
    ) -> Dict[str, Any]:
        if preferred_bot:
            selected = self.get_bot(preferred_bot)
            if not selected:
                raise ValueError(f"Bot '{preferred_bot}' not found")
            return self._build_route(selected, query, route_type="explicit_bot")

        candidate_bots = self._bots
        if preferred_category:
            category_key = preferred_category.strip().lower()
            candidate_bots = [b for b in self._bots if b.category.lower() == category_key]
            if not candidate_bots:
                raise ValueError(f"Category '{preferred_category}' not found")

        query_tokens = self._tokenize(query)
        scored: List[tuple[int, GPTBotDefinition]] = []

        for bot in candidate_bots:
            domain_text = " ".join([bot.name, bot.category, bot.purpose, bot.notes]).lower()
            score = sum(1 for token in query_tokens if token in domain_text)
            scored.append((score, bot))

        scored.sort(key=lambda item: item[0], reverse=True)
        top_score, selected = scored[0]
        route_type = "semantic_match" if top_score > 0 else "category_default"
        return self._build_route(selected, query, route_type=route_type, score=top_score)

    def _tokenize(self, text: str) -> List[str]:
        return [
            t.strip(".,!?;:()[]{}\"'").lower()
            for t in text.split()
            if len(t.strip(".,!?;:()[]{}\"'")) >= 4
        ]

    def _build_route(
        self,
        bot: GPTBotDefinition,
        query: str,
        route_type: str,
        score: int = 0,
    ) -> Dict[str, Any]:
        blueprint = self._CATEGORY_ARCHETYPES.get(
            bot.category,
            {
                "archetype": "generalist",
                "pipeline": ["intake", "analysis", "generation", "review"],
                "internal_systems": ["ORACLE", "SOCRATES"],
            },
        )
        return {
            "route_type": route_type,
            "match_score": score,
            "bot": bot.to_dict(),
            "architecture": {
                "archetype": blueprint["archetype"],
                "pipeline": list(blueprint["pipeline"]),
                "internal_systems": list(blueprint["internal_systems"]),
                "query_summary": query[:160],
            },
        }
