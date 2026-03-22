"""
Collective Intelligence — PRADYSAGICAN v2.0
Swarm learning across multiple PRADYSAGICAN instances with federated learning,
Byzantine fault-tolerant consensus, reputation systems, and adversarial detection.
"""
from __future__ import annotations

import hashlib
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


# ── Enums ────────────────────────────────────────────────────────────────────

class ConsensusProtocol(str, Enum):
    MAJORITY = "majority"
    WEIGHTED = "weighted"
    BYZANTINE_TOLERANT = "byzantine_tolerant"


class NodeStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    SUSPECTED = "suspected"  # suspected adversarial
    BANNED = "banned"


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class PeerNode:
    """A node in the collective intelligence network."""
    node_id: str
    address: str
    capabilities: list[str] = field(default_factory=list)
    reputation: float = 0.5  # 0 = untrustworthy, 1 = fully trusted
    last_seen: float = field(default_factory=time.time)
    knowledge_domains: list[str] = field(default_factory=list)
    status: NodeStatus = NodeStatus.ONLINE
    contributions: int = 0
    violations: int = 0


@dataclass
class KnowledgeShard:
    """A piece of knowledge shared between peers."""
    id: str
    domain: str
    content_hash: str
    metadata: dict[str, Any] = field(default_factory=dict)
    source_node: str = ""
    timestamp: float = field(default_factory=time.time)
    confidence: float = 0.5
    validations: int = 0  # how many peers validated this

    @staticmethod
    def compute_hash(content: str) -> str:
        """Compute content hash for integrity checking."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class SwarmResult:
    """Result from a collective intelligence operation."""
    solution: Any
    participating_nodes: int
    consensus_achieved: bool
    confidence: float
    method: str
    dissent_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FederatedUpdate:
    """A model parameter update from a single node (federated learning)."""
    node_id: str
    parameters: dict[str, float]
    sample_count: int = 0
    epoch: int = 0
    loss: float = 0.0


# ── Collective Intelligence ──────────────────────────────────────────────────

class CollectiveIntelligence:
    """Swarm learning across multiple PRADYSAGICAN instances.

    Features:
    - Peer registration and discovery
    - Knowledge sharing without raw data exchange
    - Multi-protocol consensus (majority, weighted, BFT)
    - Federated learning (aggregate updates, not data)
    - Reputation system with decay and violation tracking
    - Adversarial node detection
    - Distributed problem solving with solution merging
    """

    def __init__(self, self_node_id: str | None = None) -> None:
        self._self_id = self_node_id or f"node_{uuid.uuid4().hex[:8]}"
        self._peers: dict[str, PeerNode] = {}
        self._knowledge: dict[str, KnowledgeShard] = {}
        self._rng = np.random.default_rng()

    @property
    def self_id(self) -> str:
        return self._self_id

    # ── Peer Management ──────────────────────────────────────────────────

    async def register_peer(self, node: PeerNode) -> PeerNode:
        """Add a peer to the network."""
        self._peers[node.node_id] = node
        logger.info("Peer registered: %s at %s", node.node_id, node.address)
        return node

    async def remove_peer(self, node_id: str) -> bool:
        """Remove a peer from the network."""
        if node_id in self._peers:
            del self._peers[node_id]
            return True
        return False

    def get_active_peers(self) -> list[PeerNode]:
        """Get all non-banned peers."""
        return [p for p in self._peers.values() if p.status not in (NodeStatus.BANNED, NodeStatus.OFFLINE)]

    # ── Knowledge Sharing ────────────────────────────────────────────────

    async def share_knowledge(self, shard: KnowledgeShard) -> dict[str, Any]:
        """Broadcast a knowledge shard to the collective pool."""
        self._knowledge[shard.id] = shard
        active_peers = self.get_active_peers()

        # Simulate broadcasting to peers
        received_by = []
        for peer in active_peers:
            # Peer accepts if domain matches their knowledge areas or they're generalists
            if not peer.knowledge_domains or shard.domain in peer.knowledge_domains:
                received_by.append(peer.node_id)

        return {
            "shard_id": shard.id,
            "domain": shard.domain,
            "broadcast_to": len(active_peers),
            "received_by": len(received_by),
            "confidence": shard.confidence,
        }

    async def request_knowledge(
        self,
        domain: str,
        query: str,
    ) -> list[KnowledgeShard]:
        """Ask the collective for knowledge on a domain/query."""
        # Search local knowledge pool
        results: list[KnowledgeShard] = []
        query_lower = query.lower()

        for shard in self._knowledge.values():
            if shard.domain == domain:
                results.append(shard)
            elif query_lower in str(shard.metadata).lower():
                results.append(shard)

        # Sort by confidence × validations
        results.sort(key=lambda s: s.confidence * (1 + s.validations), reverse=True)
        return results

    # ── Consensus ────────────────────────────────────────────────────────

    async def consensus(
        self,
        proposals: list[dict[str, Any]],
        protocol: ConsensusProtocol = ConsensusProtocol.MAJORITY,
    ) -> SwarmResult:
        """Reach agreement on proposals using specified protocol.

        Each proposal has a 'value' and optional 'node_id'.
        """
        if not proposals:
            return SwarmResult(
                solution=None, participating_nodes=0,
                consensus_achieved=False, confidence=0.0, method=protocol.value,
            )

        if protocol == ConsensusProtocol.MAJORITY:
            return await self._majority_vote(proposals)
        elif protocol == ConsensusProtocol.WEIGHTED:
            return await self._weighted_vote(proposals)
        elif protocol == ConsensusProtocol.BYZANTINE_TOLERANT:
            return await self._bft_consensus(proposals)
        else:
            return await self._majority_vote(proposals)

    async def _majority_vote(self, proposals: list[dict[str, Any]]) -> SwarmResult:
        """Simple majority vote consensus."""
        vote_counts: dict[str, int] = {}
        for p in proposals:
            val = str(p.get("value", ""))
            vote_counts[val] = vote_counts.get(val, 0) + 1

        total = len(proposals)
        winner = max(vote_counts, key=vote_counts.get)  # type: ignore[arg-type]
        winner_votes = vote_counts[winner]
        achieved = winner_votes > total / 2

        return SwarmResult(
            solution=winner,
            participating_nodes=total,
            consensus_achieved=achieved,
            confidence=round(winner_votes / total, 3),
            method="majority",
            dissent_count=total - winner_votes,
        )

    async def _weighted_vote(self, proposals: list[dict[str, Any]]) -> SwarmResult:
        """Reputation-weighted voting."""
        weighted_votes: dict[str, float] = {}
        total_weight = 0.0

        for p in proposals:
            val = str(p.get("value", ""))
            node_id = p.get("node_id", "")
            peer = self._peers.get(node_id)
            weight = peer.reputation if peer else 0.5
            weighted_votes[val] = weighted_votes.get(val, 0.0) + weight
            total_weight += weight

        winner = max(weighted_votes, key=weighted_votes.get)  # type: ignore[arg-type]
        winner_weight = weighted_votes[winner]
        achieved = winner_weight > total_weight / 2

        return SwarmResult(
            solution=winner,
            participating_nodes=len(proposals),
            consensus_achieved=achieved,
            confidence=round(winner_weight / max(total_weight, 0.001), 3),
            method="weighted",
            dissent_count=sum(1 for p in proposals if str(p.get("value", "")) != winner),
        )

    async def _bft_consensus(self, proposals: list[dict[str, Any]]) -> SwarmResult:
        """Byzantine Fault Tolerant consensus.

        Tolerates up to f = ⌊(n-1)/3⌋ malicious nodes.
        Requires 2f+1 agreement for consensus (i.e., > 2/3 majority).
        """
        n = len(proposals)
        f = (n - 1) // 3  # max tolerated Byzantine nodes
        required = 2 * f + 1

        # Filter out suspected adversarial nodes
        trusted_proposals = []
        for p in proposals:
            node_id = p.get("node_id", "")
            peer = self._peers.get(node_id)
            if peer and peer.status == NodeStatus.SUSPECTED:
                continue  # exclude suspected nodes
            trusted_proposals.append(p)

        vote_counts: dict[str, int] = {}
        for p in trusted_proposals:
            val = str(p.get("value", ""))
            vote_counts[val] = vote_counts.get(val, 0) + 1

        if not vote_counts:
            return SwarmResult(
                solution=None, participating_nodes=n,
                consensus_achieved=False, confidence=0.0,
                method="byzantine_tolerant",
            )

        winner = max(vote_counts, key=vote_counts.get)  # type: ignore[arg-type]
        winner_votes = vote_counts[winner]
        achieved = winner_votes >= required

        return SwarmResult(
            solution=winner,
            participating_nodes=n,
            consensus_achieved=achieved,
            confidence=round(winner_votes / max(n, 1), 3),
            method="byzantine_tolerant",
            dissent_count=n - winner_votes,
            metadata={
                "byzantine_tolerance": f,
                "required_agreement": required,
                "trusted_voters": len(trusted_proposals),
            },
        )

    # ── Federated Learning ───────────────────────────────────────────────

    async def federated_learn(
        self,
        model_updates: list[FederatedUpdate],
    ) -> dict[str, Any]:
        """Aggregate model updates using federated averaging.

        Averages parameter updates weighted by sample count,
        without ever exchanging raw training data.
        """
        if not model_updates:
            return {"error": "No updates to aggregate"}

        # Collect all parameter names
        all_params: set[str] = set()
        for update in model_updates:
            all_params.update(update.parameters.keys())

        # Weighted average by sample count
        total_samples = sum(u.sample_count for u in model_updates)
        if total_samples == 0:
            total_samples = len(model_updates)
            for u in model_updates:
                u.sample_count = 1

        aggregated: dict[str, float] = {}
        for param in all_params:
            weighted_sum = 0.0
            for update in model_updates:
                weight = update.sample_count / total_samples
                val = update.parameters.get(param, 0.0)
                weighted_sum += val * weight
            aggregated[param] = round(weighted_sum, 6)

        # Track convergence: variance across updates
        variances: dict[str, float] = {}
        for param in all_params:
            values = [u.parameters.get(param, 0.0) for u in model_updates]
            variances[param] = round(float(np.var(values)), 6)

        avg_loss = float(np.mean([u.loss for u in model_updates]))
        converging = avg_loss < 0.5  # simple threshold

        return {
            "aggregated_params": aggregated,
            "participating_nodes": len(model_updates),
            "total_samples": total_samples,
            "avg_loss": round(avg_loss, 4),
            "parameter_variance": variances,
            "converging": converging,
        }

    # ── Reputation System ────────────────────────────────────────────────

    async def reputation_update(
        self,
        node_id: str,
        success: bool,
        magnitude: float = 0.1,
    ) -> dict[str, Any]:
        """Update peer reputation based on contribution quality."""
        peer = self._peers.get(node_id)
        if not peer:
            return {"error": f"Peer not found: {node_id}"}

        if success:
            peer.reputation = min(peer.reputation + magnitude, 1.0)
            peer.contributions += 1
        else:
            peer.reputation = max(peer.reputation - magnitude * 1.5, 0.0)
            peer.violations += 1

        peer.last_seen = time.time()

        # Auto-suspect if reputation drops too low
        if peer.reputation < 0.15 and peer.violations >= 3:
            peer.status = NodeStatus.SUSPECTED
            logger.warning("Peer %s suspected adversarial (reputation=%.2f)", node_id, peer.reputation)

        # Auto-ban if extremely low
        if peer.reputation < 0.05 and peer.violations >= 5:
            peer.status = NodeStatus.BANNED
            logger.warning("Peer %s banned (reputation=%.2f)", node_id, peer.reputation)

        return {
            "node_id": node_id,
            "reputation": round(peer.reputation, 3),
            "status": peer.status.value,
            "contributions": peer.contributions,
            "violations": peer.violations,
        }

    # ── Adversarial Detection ────────────────────────────────────────────

    async def detect_adversarial(self, node_id: str) -> dict[str, Any]:
        """Detect if a peer is providing bad or malicious data.

        Uses multiple signals: reputation, violation rate, knowledge quality.
        """
        peer = self._peers.get(node_id)
        if not peer:
            return {"error": f"Peer not found: {node_id}"}

        total_interactions = peer.contributions + peer.violations
        violation_rate = peer.violations / max(total_interactions, 1)

        # Check knowledge quality from this node
        node_shards = [s for s in self._knowledge.values() if s.source_node == node_id]
        avg_confidence = float(np.mean([s.confidence for s in node_shards])) if node_shards else 0.5
        avg_validations = float(np.mean([s.validations for s in node_shards])) if node_shards else 0.0

        # Adversarial score: higher = more suspicious
        suspicion_score = (
            (1.0 - peer.reputation) * 0.4
            + violation_rate * 0.3
            + (1.0 - avg_confidence) * 0.2
            + (1.0 / (1.0 + avg_validations)) * 0.1
        )

        is_adversarial = suspicion_score > 0.7
        recommendation = (
            "ban" if suspicion_score > 0.85
            else "investigate" if suspicion_score > 0.6
            else "monitor" if suspicion_score > 0.4
            else "trusted"
        )

        return {
            "node_id": node_id,
            "suspicion_score": round(suspicion_score, 3),
            "is_adversarial": is_adversarial,
            "recommendation": recommendation,
            "signals": {
                "reputation": round(peer.reputation, 3),
                "violation_rate": round(violation_rate, 3),
                "avg_knowledge_confidence": round(avg_confidence, 3),
                "avg_validations": round(avg_validations, 1),
            },
        }

    # ── Swarm Problem Solving ────────────────────────────────────────────

    async def swarm_solve(
        self,
        problem: str,
        protocol: ConsensusProtocol = ConsensusProtocol.WEIGHTED,
    ) -> SwarmResult:
        """Distribute a problem across peers and merge solutions.

        Each active peer generates a candidate solution (simulated),
        then consensus determines the best answer.
        """
        active = self.get_active_peers()
        if not active:
            return SwarmResult(
                solution=None, participating_nodes=0,
                consensus_achieved=False, confidence=0.0,
                method="swarm_solve",
            )

        # Each peer produces a candidate solution (simulated)
        proposals: list[dict[str, Any]] = []
        rng = np.random.default_rng(hash(problem) % (2**31))

        for peer in active:
            # Solution quality correlates with reputation and domain relevance
            domain_match = any(d in problem.lower() for d in peer.knowledge_domains) if peer.knowledge_domains else False
            quality = peer.reputation * (1.3 if domain_match else 0.8) + rng.uniform(-0.1, 0.1)
            quality = max(0.0, min(1.0, quality))

            proposals.append({
                "value": f"solution_by_{peer.node_id}",
                "node_id": peer.node_id,
                "quality": round(float(quality), 3),
            })

        # Select best solution by quality, then validate with consensus
        proposals.sort(key=lambda p: p.get("quality", 0), reverse=True)
        best = proposals[0]

        # Consensus on the best solution
        consensus_proposals = [{"value": best["value"], "node_id": p["node_id"]} for p in proposals[:len(proposals)]]
        # Simulate: peers above median quality agree with best
        median_quality = float(np.median([p["quality"] for p in proposals]))
        agreement_proposals = [
            {"value": best["value"], "node_id": p["node_id"]}
            if p["quality"] >= median_quality
            else {"value": f"alt_solution_{p['node_id']}", "node_id": p["node_id"]}
            for p in proposals
        ]

        consensus_result = await self.consensus(agreement_proposals, protocol)

        return SwarmResult(
            solution=best["value"],
            participating_nodes=len(active),
            consensus_achieved=consensus_result.consensus_achieved,
            confidence=round(best.get("quality", 0.5), 3),
            method="swarm_solve",
            dissent_count=consensus_result.dissent_count,
            metadata={
                "best_quality": best["quality"],
                "best_node": best["node_id"],
                "protocol": protocol.value,
            },
        )

    # ── Stats ────────────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        peers = list(self._peers.values())
        return {
            "self_id": self._self_id,
            "total_peers": len(peers),
            "active_peers": sum(1 for p in peers if p.status == NodeStatus.ONLINE),
            "suspected_peers": sum(1 for p in peers if p.status == NodeStatus.SUSPECTED),
            "banned_peers": sum(1 for p in peers if p.status == NodeStatus.BANNED),
            "knowledge_shards": len(self._knowledge),
            "avg_reputation": round(float(np.mean([p.reputation for p in peers])), 3) if peers else 0.0,
        }
