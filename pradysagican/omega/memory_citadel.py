"""12-tier memory citadel scaffolds with unified routing API."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MemoryTierSpec:
    tier: int
    name: str
    duration: str
    capacity: str


TIER_SPECS: list[MemoryTierSpec] = [
    MemoryTierSpec(0, "sensory_buffer", "500ms", "real_time_stream"),
    MemoryTierSpec(1, "working_memory", "30s", "7_plus_minus_2"),
    MemoryTierSpec(2, "episodic_memory", "sessions", "unlimited"),
    MemoryTierSpec(3, "semantic_memory", "permanent", "100m_triples"),
    MemoryTierSpec(4, "procedural_memory", "permanent", "10k_skills"),
    MemoryTierSpec(5, "prospective_memory", "task_bound", "1k_pending"),
    MemoryTierSpec(6, "somatic_memory", "long_term", "unlimited"),
    MemoryTierSpec(7, "metacognitive_memory", "long_term", "unlimited"),
    MemoryTierSpec(8, "causal_memory", "permanent", "1m_edges"),
    MemoryTierSpec(9, "world_model_memory", "live", "continuous"),
    MemoryTierSpec(10, "hdc_memory", "permanent", "2_power_10000"),
    MemoryTierSpec(11, "constant_state", "live", "one_tensor"),
]


class TierRouter:
    """Routes queries to likely memory tiers."""

    def route(self, query: str) -> int:
        q = query.lower()
        if any(k in q for k in ["how to", "procedure", "skill"]):
            return 4
        if any(k in q for k in ["what happened", "yesterday", "last time"]):
            return 2
        if any(k in q for k in ["fact", "true", "definition"]):
            return 3
        if any(k in q for k in ["cause", "because", "intervention"]):
            return 8
        return 1


class MemoryCitadelAPI:
    """Unified memory API hiding tier internals."""

    def __init__(self) -> None:
        self._router = TierRouter()
        self._store: dict[int, list[dict[str, Any]]] = {spec.tier: [] for spec in TIER_SPECS}
        self._seq = 0
        self._replay_buffer: list[dict[str, Any]] = []
        self._replay_limit = 500

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    @staticmethod
    def _public_entry(entry: dict[str, Any]) -> dict[str, Any]:
        out = dict(entry)
        out.pop("_citadel_meta", None)
        return out

    @staticmethod
    def _entry_fingerprint(entry: dict[str, Any]) -> str:
        clean = dict(entry)
        clean.pop("_citadel_meta", None)
        payload = repr(sorted(clean.items())).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _memory_identity(entry: dict[str, Any]) -> str | None:
        if "fact_id" in entry:
            return f"fact_id:{entry['fact_id']}"
        if "key" in entry:
            return f"key:{entry['key']}"
        if "entity" in entry and "attribute" in entry:
            return f"entity_attr:{entry['entity']}::{entry['attribute']}"
        return None

    @staticmethod
    def _memory_value(entry: dict[str, Any]) -> str:
        if "value" in entry:
            return str(entry["value"])
        if "content" in entry:
            return str(entry["content"])
        if "summary" in entry:
            return str(entry["summary"])
        return repr({k: v for k, v in entry.items() if k != "_citadel_meta"})

    def _record_replay(self, tier: int, entry: dict[str, Any]) -> None:
        self._replay_buffer.append(
            {
                "tier": tier,
                "entry": self._public_entry(entry),
                "seq": entry.get("_citadel_meta", {}).get("seq", 0),
                "importance": float(entry.get("importance", 0.5)),
            }
        )
        if len(self._replay_buffer) > self._replay_limit:
            self._replay_buffer = self._replay_buffer[-self._replay_limit :]

    def store(self, query_hint: str, payload: dict[str, Any]) -> dict[str, Any]:
        tier = self._router.route(query_hint)
        entry = dict(payload)
        entry["_citadel_meta"] = {
            "seq": self._next_seq(),
            "source_tier": tier,
            "compressed": bool(entry.get("compressed", False)),
        }
        self._store[tier].append(entry)
        self._record_replay(tier, entry)
        return {"tier": tier, "stored": True, "size": len(self._store[tier])}

    def retrieve(self, query: str, limit: int = 5, include_metadata: bool = False) -> dict[str, Any]:
        tier = self._router.route(query)
        items = self._store.get(tier, [])[-limit:]
        if include_metadata:
            return {"tier": tier, "items": [dict(i) for i in items]}
        return {"tier": tier, "items": [self._public_entry(i) for i in items]}

    def consolidate(self) -> dict[str, Any]:
        # Episodic -> semantic consolidation with duplicate suppression.
        moved = min(len(self._store[2]), 10)
        skipped_duplicates = 0
        semantic_fingerprints = {self._entry_fingerprint(e) for e in self._store[3]}
        for _ in range(moved):
            candidate = self._store[2].pop(0)
            fp = self._entry_fingerprint(candidate)
            if fp in semantic_fingerprints:
                skipped_duplicates += 1
                continue
            semantic_fingerprints.add(fp)
            self._store[3].append(candidate)
        return {"moved_episodic_to_semantic": moved - skipped_duplicates, "skipped_duplicates": skipped_duplicates}

    def garbage_collect(self, max_entries_per_tier: int = 250, keep_recent: int = 5) -> dict[str, Any]:
        removed_duplicates = 0
        removed_capacity = 0
        for tier, entries in self._store.items():
            if not entries:
                continue
            deduped_rev: list[dict[str, Any]] = []
            seen: set[str] = set()
            for entry in reversed(entries):
                fp = self._entry_fingerprint(entry)
                if fp in seen:
                    removed_duplicates += 1
                    continue
                seen.add(fp)
                deduped_rev.append(entry)
            deduped = list(reversed(deduped_rev))
            if len(deduped) > max_entries_per_tier:
                keep = max(keep_recent, max_entries_per_tier)
                removed_capacity += len(deduped) - keep
                deduped = deduped[-keep:]
            self._store[tier] = deduped
        return {"removed_duplicates": removed_duplicates, "removed_capacity": removed_capacity}

    def synchronize(self, source_tier: int = 3, target_tiers: tuple[int, ...] = (1, 2)) -> dict[str, Any]:
        source = self._store.get(source_tier, [])
        source_latest: dict[str, dict[str, Any]] = {}
        for entry in source:
            identity = self._memory_identity(entry)
            if identity:
                source_latest[identity] = entry
        if not source_latest:
            return {"invalidated": 0, "synced": 0}

        invalidated = 0
        synced = 0
        for tier in target_tiers:
            bucket = self._store.get(tier, [])
            kept: list[dict[str, Any]] = []
            seen_identities: set[str] = set()
            for entry in bucket:
                identity = self._memory_identity(entry)
                if identity and identity in source_latest:
                    if self._memory_value(entry) != self._memory_value(source_latest[identity]):
                        invalidated += 1
                        continue
                    seen_identities.add(identity)
                kept.append(entry)
            for identity, src_entry in source_latest.items():
                if identity in seen_identities:
                    continue
                copied = dict(src_entry)
                copied_meta = dict(copied.get("_citadel_meta", {}))
                copied_meta["synced_from_tier"] = source_tier
                copied_meta["seq"] = self._next_seq()
                copied["_citadel_meta"] = copied_meta
                kept.append(copied)
                synced += 1
            self._store[tier] = kept
        return {"invalidated": invalidated, "synced": synced}

    def compress_tier(
        self,
        tier: int = 2,
        target_tier: int = 3,
        group_size: int = 5,
        keep_recent: int = 5,
    ) -> dict[str, Any]:
        entries = self._store.get(tier, [])
        if len(entries) <= keep_recent:
            return {"compressed_groups": 0, "removed_entries": 0, "target_tier": target_tier}
        candidates = entries[:-keep_recent]
        compressed_groups = 0
        removed_entries = 0
        for i in range(0, len(candidates), max(1, group_size)):
            chunk = candidates[i : i + max(1, group_size)]
            if not chunk:
                continue
            compressed_groups += 1
            removed_entries += len(chunk)
            snippets = []
            for entry in chunk:
                pub = self._public_entry(entry)
                if "content" in pub:
                    snippets.append(str(pub["content"]))
                elif "summary" in pub:
                    snippets.append(str(pub["summary"]))
                else:
                    snippets.append(repr(pub))
            summary = {
                "summary": " | ".join(snippets)[:400],
                "source_tier": tier,
                "source_count": len(chunk),
                "compressed": True,
                "_citadel_meta": {"seq": self._next_seq(), "source_tier": target_tier, "compressed": True},
            }
            self._store[target_tier].append(summary)
            self._record_replay(target_tier, summary)
        self._store[tier] = entries[-keep_recent:]
        return {"compressed_groups": compressed_groups, "removed_entries": removed_entries, "target_tier": target_tier}

    def rehearse(self, sample_size: int = 5, strategy: str = "priority", tier: int | None = None) -> dict[str, Any]:
        if sample_size <= 0:
            return {"items": [], "count": 0, "strategy": strategy}
        if tier is not None:
            candidates = [
                {
                    "tier": tier,
                    "entry": self._public_entry(e),
                    "seq": e.get("_citadel_meta", {}).get("seq", 0),
                    "importance": float(e.get("importance", 0.5)),
                }
                for e in self._store.get(tier, [])
            ]
        else:
            candidates = list(self._replay_buffer)
        if not candidates:
            return {"items": [], "count": 0, "strategy": strategy}

        if strategy == "random":
            picked = random.sample(candidates, k=min(sample_size, len(candidates)))
        else:
            picked = sorted(candidates, key=lambda x: (x["importance"], x["seq"]), reverse=True)[:sample_size]
        return {"items": [p["entry"] for p in picked], "count": len(picked), "strategy": strategy}
