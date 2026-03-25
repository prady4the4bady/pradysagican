"""
F611: AUTO-RL - Automated Reinforcement Learning from Failures
===============================================================

Extracts principles from failure trajectories and stores them for retrieval:
- Failure trajectory extraction
- Principle generation from patterns
- ChromaDB semantic storage with embeddings
- Retrieval with similarity search
- Confidence reinforcement through repeated access
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class FailureCategory(str, Enum):
    """Categories of failures."""
    TIMEOUT = "timeout"
    ASSERTION_FAILED = "assertion_failed"
    TYPE_ERROR = "type_error"
    VALUE_ERROR = "value_error"
    RESOURCE_EXCEEDED = "resource_exceeded"
    LOGIC_ERROR = "logic_error"
    EXTERNAL_API = "external_api"
    CONCURRENCY = "concurrency"


@dataclass
class FailureEvent:
    """A single failure event in execution."""
    failure_id: str
    category: FailureCategory
    timestamp: float
    error_message: str
    stacktrace: str
    context: dict[str, Any]
    code_location: Optional[str] = None
    recovery_action: Optional[str] = None


@dataclass
class FailureTrajectory:
    """A sequence of related failure events."""
    trajectory_id: str
    events: list[FailureEvent] = field(default_factory=list)
    root_cause: Optional[str] = None
    resolution: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    resolution_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_event(self, event: FailureEvent) -> None:
        """Add failure event to trajectory."""
        self.events.append(event)
        logger.debug("Added event to trajectory %s: %s", self.trajectory_id, event.category.value)


@dataclass
class Principle:
    """A learned principle from failures."""
    principle_id: str
    category: FailureCategory
    description: str
    pattern: str  # Regular expression or pattern description
    remediation: str  # How to fix/prevent
    confidence: float  # 0.0-1.0, increases with reinforcement
    embedding: Optional[list[float]] = None
    extraction_timestamp: float = field(default_factory=time.time)
    last_reinforced: float = field(default_factory=time.time)
    reinforcement_count: int = 0
    source_trajectories: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def reinforce(self) -> None:
        """Increase confidence through reinforcement."""
        self.last_reinforced = time.time()
        self.reinforcement_count += 1
        # Confidence grows logarithmically with reinforcements
        import math
        self.confidence = min(0.99, 0.5 + 0.49 * math.log1p(self.reinforcement_count) / 5.0)


@dataclass
class RetrievalResult:
    """Result from principle retrieval."""
    principle: Principle
    similarity_score: float  # 0.0-1.0
    relevance_score: float  # Based on confidence and recency
    applied: bool = False
    application_result: Optional[str] = None


class AutoRL:
    """Automated Reinforcement Learning from failure trajectories."""

    def __init__(
        self,
        storage_dir: Optional[Path] = None,
        use_chroma: bool = False,
    ):
        """
        Initialize AutoRL system.
        
        Args:
            storage_dir: Directory for storing trajectories and principles
            use_chroma: Whether to use ChromaDB for semantic search
        """
        self.storage_dir = storage_dir or Path("./data/auto_rl")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.use_chroma = use_chroma
        self._chroma_client = None
        
        # In-memory storage
        self._trajectories: dict[str, FailureTrajectory] = {}
        self._principles: dict[str, Principle] = {}
        
        # Initialize ChromaDB if available
        if use_chroma:
            self._init_chroma()
        
        self._load_storage()
        logger.info("AutoRL initialized: storage=%s, chroma=%s", self.storage_dir, use_chroma)

    def _init_chroma(self) -> None:
        """Initialize ChromaDB client."""
        try:
            import chromadb
            self._chroma_client = chromadb.PersistentClient(
                path=str(self.storage_dir / "chromadb")
            )
            logger.info("ChromaDB initialized")
        except ImportError:
            logger.warning("ChromaDB not available; using local storage only")
            self.use_chroma = False
        except Exception as exc:
            logger.warning("Failed to initialize ChromaDB: %s", exc)
            self.use_chroma = False

    def record_failure_trajectory(
        self,
        trajectory_id: str,
        events: list[FailureEvent],
        root_cause: Optional[str] = None,
        resolution: Optional[str] = None,
        resolution_time_ms: float = 0.0,
    ) -> FailureTrajectory:
        """
        Record a failure trajectory.
        
        Args:
            trajectory_id: Unique ID for trajectory
            events: List of failure events
            root_cause: Identified root cause
            resolution: How trajectory was resolved
            resolution_time_ms: Time to resolve
            
        Returns:
            Recorded FailureTrajectory
        """
        trajectory = FailureTrajectory(
            trajectory_id=trajectory_id,
            events=events,
            root_cause=root_cause,
            resolution=resolution,
            resolution_time_ms=resolution_time_ms,
        )
        
        self._trajectories[trajectory_id] = trajectory
        logger.info("Recorded trajectory %s with %d events", trajectory_id, len(events))
        
        return trajectory

    async def extract_principles(self, trajectory: FailureTrajectory) -> list[Principle]:
        """
        Extract principles from a failure trajectory.
        
        Args:
            trajectory: Failure trajectory to analyze
            
        Returns:
            List of extracted principles
        """
        principles = []
        
        for i, event in enumerate(trajectory.events):
            # Analyze each failure event
            principle = await self._analyze_failure_event(event, trajectory, i)
            if principle:
                principles.append(principle)
        
        # Analyze trajectory patterns
        trajectory_principle = await self._analyze_trajectory_pattern(trajectory)
        if trajectory_principle:
            principles.append(trajectory_principle)
        
        # Store principles
        for principle in principles:
            self._store_principle(principle, trajectory.trajectory_id)
            logger.debug("Extracted principle: %s (confidence: %.2f)", principle.principle_id, principle.confidence)
        
        logger.info("Extracted %d principles from trajectory %s", len(principles), trajectory.trajectory_id)
        return principles

    async def _analyze_failure_event(
        self,
        event: FailureEvent,
        trajectory: FailureTrajectory,
        event_index: int
    ) -> Optional[Principle]:
        """Analyze a single failure event."""
        principle_id = f"principle_{int(time.time() * 1000)}_{event_index}"
        
        # Generate principle description
        description = f"Handle {event.category.value}: {event.error_message[:100]}"
        
        # Create pattern
        pattern = self._generate_pattern(event.error_message)
        
        # Create remediation
        remediation = self._generate_remediation(event.category, event.error_message)
        
        principle = Principle(
            principle_id=principle_id,
            category=event.category,
            description=description,
            pattern=pattern,
            remediation=remediation,
            confidence=0.6,  # Initial confidence
            source_trajectories=[trajectory.trajectory_id],
        )
        
        # Generate embedding if using ChromaDB
        if self.use_chroma:
            principle.embedding = await self._generate_embedding(description)
        
        return principle

    async def _analyze_trajectory_pattern(self, trajectory: FailureTrajectory) -> Optional[Principle]:
        """Analyze patterns across multiple events in trajectory."""
        if len(trajectory.events) < 2:
            return None
        
        # Identify common failure categories
        categories = [e.category for e in trajectory.events]
        category_counts = {}
        for cat in categories:
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        most_common = max(category_counts, key=category_counts.get)
        
        principle_id = f"pattern_{trajectory.trajectory_id}"
        description = f"Trajectory pattern: Multiple {most_common.value} failures detected"
        
        principle = Principle(
            principle_id=principle_id,
            category=most_common,
            description=description,
            pattern=f"repeated_{most_common.value}_pattern",
            remediation=f"Implement cascading safeguards for {most_common.value}",
            confidence=0.5 + 0.1 * len(trajectory.events),
            source_trajectories=[trajectory.trajectory_id],
        )
        
        if self.use_chroma:
            principle.embedding = await self._generate_embedding(description)
        
        return principle

    def _generate_pattern(self, error_message: str) -> str:
        """Generate a pattern from error message."""
        # Simple heuristic: use first part of error
        pattern = error_message.split("\n")[0][:100]
        return f"^{pattern}.*"

    def _generate_remediation(self, category: FailureCategory, error_msg: str) -> str:
        """Generate remediation action for failure category."""
        remediation_map = {
            FailureCategory.TIMEOUT: "Implement timeout handling and cancellation logic",
            FailureCategory.ASSERTION_FAILED: "Review assumptions and add validation",
            FailureCategory.TYPE_ERROR: "Add type hints and validation",
            FailureCategory.VALUE_ERROR: "Add bounds checking and value validation",
            FailureCategory.RESOURCE_EXCEEDED: "Implement resource limits and cleanup",
            FailureCategory.LOGIC_ERROR: "Review algorithm logic and test cases",
            FailureCategory.EXTERNAL_API: "Add retry logic and error handling",
            FailureCategory.CONCURRENCY: "Review synchronization and race conditions",
        }
        return remediation_map.get(category, "Debug and add error handling")

    async def _generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text using simple TF-IDF simulation."""
        # Simple hash-based embedding simulation (17 dimensions)
        import hashlib
        hash_bytes = hashlib.sha256(text.encode()).digest()
        embedding = [float(b) / 255.0 for b in hash_bytes[:17]]
        return embedding

    def _store_principle(self, principle: Principle, source_trajectory_id: str) -> None:
        """Store a principle in archive."""
        self._principles[principle.principle_id] = principle
        
        # Store in ChromaDB if available
        if self.use_chroma and self._chroma_client and principle.embedding:
            try:
                collection = self._chroma_client.get_or_create_collection(
                    name="principles",
                    metadata={"hnsw:space": "cosine"}
                )
                collection.add(
                    ids=[principle.principle_id],
                    embeddings=[principle.embedding],
                    documents=[principle.description],
                    metadatas=[{
                        "category": principle.category.value,
                        "confidence": principle.confidence,
                        "remediation": principle.remediation,
                    }],
                )
            except Exception as exc:
                logger.warning("Failed to store principle in ChromaDB: %s", exc)

    async def retrieve_principles(
        self,
        query: str,
        error_category: Optional[FailureCategory] = None,
        limit: int = 5,
    ) -> list[RetrievalResult]:
        """
        Retrieve relevant principles for a failure.
        
        Args:
            query: Query string describing the failure
            error_category: Optional category filter
            limit: Maximum principles to retrieve
            
        Returns:
            List of relevant principles with scores
        """
        results = []
        
        # If using ChromaDB, query semantic similarity
        if self.use_chroma and self._chroma_client:
            try:
                import hashlib
                hash_bytes = hashlib.sha256(query.encode()).digest()
                query_embedding = [float(b) / 255.0 for b in hash_bytes[:17]]
                
                collection = self._chroma_client.get_or_create_collection(name="principles")
                chroma_results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit,
                )
                
                for i, principle_id in enumerate(chroma_results["ids"][0]):
                    if principle_id in self._principles:
                        principle = self._principles[principle_id]
                        similarity = max(0.0, chroma_results["distances"][0][i])
                        
                        # Adjust for category filter
                        if error_category and principle.category != error_category:
                            similarity *= 0.7
                        
                        results.append(
                            RetrievalResult(
                                principle=principle,
                                similarity_score=similarity,
                                relevance_score=similarity * principle.confidence,
                            )
                        )
            except Exception as exc:
                logger.warning("ChromaDB query failed: %s", exc)
        
        # Fallback: local keyword matching
        if not results:
            for principle in self._principles.values():
                if error_category and principle.category != error_category:
                    continue
                
                # Simple keyword overlap
                query_words = set(query.lower().split())
                desc_words = set(principle.description.lower().split())
                overlap = len(query_words & desc_words) / max(len(query_words), 1)
                
                if overlap > 0.2:
                    results.append(
                        RetrievalResult(
                            principle=principle,
                            similarity_score=overlap,
                            relevance_score=overlap * principle.confidence,
                        )
                    )
        
        # Sort by relevance and apply limit
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        results = results[:limit]
        
        # Reinforce accessed principles
        for result in results:
            result.principle.reinforce()
        
        logger.debug("Retrieved %d relevant principles for query", len(results))
        return results

    def get_learning_summary(self) -> dict[str, Any]:
        """Get summary of learned principles."""
        if not self._principles:
            return {"total_principles": 0}
        
        principles_list = list(self._principles.values())
        avg_confidence = sum(p.confidence for p in principles_list) / len(principles_list)
        high_confidence = len([p for p in principles_list if p.confidence > 0.8])
        
        category_distribution = {}
        for principle in principles_list:
            cat = principle.category.value
            category_distribution[cat] = category_distribution.get(cat, 0) + 1
        
        return {
            "total_principles": len(self._principles),
            "total_trajectories": len(self._trajectories),
            "avg_confidence": float(avg_confidence),
            "high_confidence_count": high_confidence,
            "total_reinforcements": sum(p.reinforcement_count for p in principles_list),
            "category_distribution": category_distribution,
            "newest_principle": max(
                (p.extraction_timestamp for p in principles_list),
                default=0
            ),
        }

    def _load_storage(self) -> None:
        """Load principles from storage."""
        principles_file = self.storage_dir / "principles.json"
        if principles_file.exists():
            try:
                with open(principles_file) as f:
                    data = json.load(f)
                    for p_data in data.get("principles", []):
                        principle = Principle(
                            principle_id=p_data["principle_id"],
                            category=FailureCategory(p_data["category"]),
                            description=p_data["description"],
                            pattern=p_data["pattern"],
                            remediation=p_data["remediation"],
                            confidence=p_data["confidence"],
                            extraction_timestamp=p_data["extraction_timestamp"],
                            last_reinforced=p_data["last_reinforced"],
                            reinforcement_count=p_data["reinforcement_count"],
                            source_trajectories=p_data["source_trajectories"],
                        )
                        self._principles[principle.principle_id] = principle
                
                logger.info("Loaded %d principles from storage", len(self._principles))
            except Exception as exc:
                logger.warning("Failed to load principles: %s", exc)

    def save_storage(self) -> None:
        """Save principles to storage."""
        principles_file = self.storage_dir / "principles.json"
        
        try:
            data = {
                "timestamp": time.time(),
                "total_principles": len(self._principles),
                "principles": [
                    {
                        "principle_id": p.principle_id,
                        "category": p.category.value,
                        "description": p.description,
                        "pattern": p.pattern,
                        "remediation": p.remediation,
                        "confidence": p.confidence,
                        "extraction_timestamp": p.extraction_timestamp,
                        "last_reinforced": p.last_reinforced,
                        "reinforcement_count": p.reinforcement_count,
                        "source_trajectories": p.source_trajectories,
                    }
                    for p in self._principles.values()
                ],
            }
            
            with open(principles_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info("Saved %d principles to storage", len(self._principles))
        except Exception as exc:
            logger.error("Failed to save principles: %s", exc)
