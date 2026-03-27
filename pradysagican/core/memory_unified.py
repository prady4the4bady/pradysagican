"""
LAYER 3: Unified Memory System
================================

7-tier hierarchical memory with automatic decay, consolidation, and retrieval.
Integrates semantic search, episodic memory, and skill learning.

Attribution:
- Hierarchical memory: MNEMOSYNE (Phase 2 implementation)
- Decay mechanisms: Ebbinghaus forgetting curve
- Consolidation: Neuroscience memory consolidation patterns
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
import json
import hashlib

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════════
# MEMORY TIERS
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class MemoryRecord:
    """Single memory record"""
    id: str
    content: str
    tier: str
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    importance: float = 0.5
    tags: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def should_decay(self) -> bool:
        """Check if this memory should decay"""
        age_hours = (datetime.now() - self.created_at).total_seconds() / 3600
        # Simple decay: halve importance every tier-specific interval
        tier_intervals = {
            'immediate': 0.5,     # 30 minutes
            'short_term': 4,      # 4 hours
            'working': 12,        # 12 hours
            'episodic': 72,       # 3 days
            'semantic': 720,      # 30 days
            'skill': 2160,        # 90 days (skills decay slower)
            'conceptual': 8640    # 1 year (concepts decay very slowly)
        }
        interval = tier_intervals.get(self.tier, 24)
        return age_hours > interval
    
    def apply_decay(self, factor: float = 0.8):
        """Apply decay factor to importance"""
        self.importance *= factor


class MemoryTier:
    """Single memory tier with capacity limits"""
    
    def __init__(self, name: str, capacity: int, ttl_minutes: int):
        self.name = name
        self.capacity = capacity
        self.ttl_minutes = ttl_minutes
        self.memories: Dict[str, MemoryRecord] = {}
    
    async def store(self, record: MemoryRecord):
        """Store memory in this tier"""
        if len(self.memories) >= self.capacity:
            # Evict least important
            least_important = min(
                self.memories.values(),
                key=lambda m: m.importance * m.access_count
            )
            del self.memories[least_important.id]
        
        self.memories[record.id] = record
    
    async def retrieve(self, query: str) -> List[MemoryRecord]:
        """Retrieve matching memories"""
        matches = []
        query_lower = query.lower()
        
        for memory in self.memories.values():
            # Simple keyword matching (would use embeddings in production)
            if query_lower in memory.content.lower():
                memory.access_count += 1
                memory.last_accessed = datetime.now()
                matches.append(memory)
        
        return sorted(matches, key=lambda m: m.importance, reverse=True)
    
    async def cleanup(self):
        """Remove expired memories"""
        now = datetime.now()
        expired = [
            mid for mid, mem in self.memories.items()
            if (now - mem.created_at) > timedelta(minutes=self.ttl_minutes)
        ]
        for mid in expired:
            del self.memories[mid]


# ════════════════════════════════════════════════════════════════════════════
# UNIFIED MEMORY MANAGER
# ════════════════════════════════════════════════════════════════════════════

class MemoryManager:
    """
    Unified memory system with 7 tiers and automatic consolidation
    """
    
    def __init__(self):
        # Define 7-tier hierarchy
        self.tiers = {
            'immediate': MemoryTier('Immediate Cache', capacity=50, ttl_minutes=5),
            'short_term': MemoryTier('Short-Term', capacity=200, ttl_minutes=60),
            'working': MemoryTier('Working Memory', capacity=1000, ttl_minutes=1440),
            'episodic': MemoryTier('Episodic', capacity=5000, ttl_minutes=43200),
            'semantic': MemoryTier('Semantic Knowledge', capacity=50000, ttl_minutes=1440*30),
            'skill': MemoryTier('Skill Tree', capacity=1000, ttl_minutes=1440*90),
            'conceptual': MemoryTier('Conceptual Models', capacity=5000, ttl_minutes=1440*365),
        }
        
        self.memory_counter = 0
        self._consolidation_task = None
    
    async def store(self, content: str, tier: str = 'working', 
                   importance: float = 0.5, tags: List[str] = None):
        """Store memory in specified tier"""
        if tier not in self.tiers:
            tier = 'working'
        
        memory_id = f"mem_{self.memory_counter}_{hashlib.md5(content.encode()).hexdigest()[:8]}"
        self.memory_counter += 1
        
        record = MemoryRecord(
            id=memory_id,
            content=content,
            tier=tier,
            importance=importance,
            tags=tags or []
        )
        
        await self.tiers[tier].store(record)
        logger.info(f"Stored memory in {tier}: {memory_id}")
        return memory_id
    
    async def retrieve(self, query: str, max_results: int = 10) -> List[MemoryRecord]:
        """Retrieve memories matching query from all tiers"""
        results = []
        
        # Search from most recent (immediate) to oldest (conceptual)
        for tier_name in ['immediate', 'short_term', 'working', 'episodic', 'semantic', 'skill', 'conceptual']:
            tier_results = await self.tiers[tier_name].retrieve(query)
            results.extend(tier_results)
        
        # Rank by importance * recency
        now = datetime.now()
        for mem in results:
            recency = 1.0 / (1.0 + (now - mem.last_accessed).total_seconds() / 3600)
            mem.importance *= recency
        
        return sorted(results, key=lambda m: m.importance, reverse=True)[:max_results]
    
    async def consolidate(self):
        """
        Consolidate memory across tiers (called periodically)
        - Decay importance in lower tiers
        - Promote important items
        - Clean up expired items
        """
        logger.info("Memory consolidation cycle starting...")
        
        # Cleanup all tiers
        for tier in self.tiers.values():
            await tier.cleanup()
        
        # Decay in working memory
        for memory in self.tiers['working'].memories.values():
            if memory.should_decay():
                memory.apply_decay(0.9)  # 10% decay
        
        # Promote important episodic memories to semantic
        for memory in list(self.tiers['episodic'].memories.values()):
            if memory.importance > 0.8 and memory.access_count > 5:
                # Move to semantic
                memory.tier = 'semantic'
                self.tiers['episodic'].memories.pop(memory.id, None)
                await self.tiers['semantic'].store(memory)
                logger.info(f"Promoted {memory.id} to semantic tier")
        
        logger.info("Memory consolidation cycle complete")
    
    async def start_consolidation_loop(self, interval_minutes: int = 60):
        """Start periodic consolidation"""
        self._consolidation_task = asyncio.create_task(
            self._consolidation_loop(interval_minutes)
        )
    
    async def _consolidation_loop(self, interval_minutes: int):
        """Background consolidation loop"""
        while True:
            await asyncio.sleep(interval_minutes * 60)
            await self.consolidate()
    
    async def stop_consolidation(self):
        """Stop consolidation loop"""
        if self._consolidation_task:
            self._consolidation_task.cancel()
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        stats = {
            'total_memories': 0,
            'by_tier': {},
            'total_importance': 0
        }
        
        for tier_name, tier in self.tiers.items():
            count = len(tier.memories)
            total_importance = sum(m.importance for m in tier.memories.values())
            stats['by_tier'][tier_name] = {
                'count': count,
                'capacity': tier.capacity,
                'utilization': f"{(count/tier.capacity)*100:.1f}%",
                'total_importance': total_importance
            }
            stats['total_memories'] += count
        
        return stats


# ════════════════════════════════════════════════════════════════════════════
# EPISODIC MEMORY STORAGE
# ════════════════════════════════════════════════════════════════════════════

class EpisodicMemory:
    """
    Record complete episodes/conversations with full context
    """
    
    def __init__(self):
        self.episodes: Dict[str, Dict[str, Any]] = {}
        self.episode_counter = 0
    
    async def record_episode(self, query: str, reasoning_trace: str, 
                            result: str, metrics: Dict[str, Any]):
        """Record complete episode"""
        episode_id = f"ep_{self.episode_counter}"
        self.episode_counter += 1
        
        episode = {
            'id': episode_id,
            'query': query,
            'reasoning': reasoning_trace,
            'result': result,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat(),
        }
        
        self.episodes[episode_id] = episode
        return episode_id
    
    async def retrieve_similar_episodes(self, query: str, limit: int = 5) -> List[Dict]:
        """Retrieve similar past episodes"""
        query_lower = query.lower()
        matches = []
        
        for episode in self.episodes.values():
            if query_lower in episode['query'].lower():
                matches.append(episode)
        
        return matches[:limit]


# ════════════════════════════════════════════════════════════════════════════
# SEMANTIC KNOWLEDGE GRAPH
# ════════════════════════════════════════════════════════════════════════════

class SemanticKnowledge:
    """
    Semantic knowledge representation and retrieval
    """
    
    def __init__(self):
        self.knowledge: Dict[str, Dict[str, Any]] = {}
        self.relationships: List[Tuple[str, str, str]] = []  # (entity1, relation, entity2)
    
    async def add_fact(self, subject: str, predicate: str, obj: str):
        """Add semantic fact"""
        if subject not in self.knowledge:
            self.knowledge[subject] = {'predicates': {}}
        
        if predicate not in self.knowledge[subject]['predicates']:
            self.knowledge[subject]['predicates'][predicate] = []
        
        self.knowledge[subject]['predicates'][predicate].append(obj)
        self.relationships.append((subject, predicate, obj))
    
    async def query_fact(self, subject: str, predicate: str) -> List[str]:
        """Query semantic facts"""
        if subject in self.knowledge:
            return self.knowledge[subject]['predicates'].get(predicate, [])
        return []
    
    async def find_related(self, entity: str, max_depth: int = 2) -> List[str]:
        """Find all related entities"""
        related = set()
        current_level = {entity}
        
        for _ in range(max_depth):
            next_level = set()
            for ent in current_level:
                # Find forward relations
                for rel in self.relationships:
                    if rel[0] == ent:
                        next_level.add(rel[2])
                    elif rel[2] == ent:
                        next_level.add(rel[0])
            related.update(next_level)
            current_level = next_level
        
        return list(related)


# ════════════════════════════════════════════════════════════════════════════
# SKILL MEMORY TREE
# ════════════════════════════════════════════════════════════════════════════

class SkillMemory:
    """
    Learning-focused memory for skill acquisition and mastery tracking
    """
    
    def __init__(self):
        self.skills: Dict[str, Dict[str, Any]] = {}
    
    async def learn_skill(self, skill_name: str, category: str, description: str):
        """Record new skill"""
        self.skills[skill_name] = {
            'name': skill_name,
            'category': category,
            'description': description,
            'xp': 0,
            'level': 1,
            'mastery': 0.0,
            'created_at': datetime.now().isoformat(),
            'last_used': datetime.now().isoformat(),
            'usage_count': 0
        }
    
    async def use_skill(self, skill_name: str, xp_gained: int = 10):
        """Record skill usage and XP"""
        if skill_name in self.skills:
            skill = self.skills[skill_name]
            skill['xp'] += xp_gained
            skill['usage_count'] += 1
            skill['last_used'] = datetime.now().isoformat()
            
            # Level up every 100 XP
            skill['level'] = 1 + (skill['xp'] // 100)
            skill['mastery'] = min(1.0, skill['xp'] / 1000)  # Max 1.0 at 1000 XP
    
    async def get_top_skills(self, limit: int = 10) -> List[Dict]:
        """Get most mastered skills"""
        sorted_skills = sorted(
            self.skills.values(),
            key=lambda s: s['mastery'],
            reverse=True
        )
        return sorted_skills[:limit]


# ════════════════════════════════════════════════════════════════════════════
# TEST & DEMO
# ════════════════════════════════════════════════════════════════════════════

async def demo_memory_system():
    """Demonstrate memory system"""
    print("\n" + "="*70)
    print("LAYER 3: MEMORY SYSTEM DEMO")
    print("="*70 + "\n")
    
    manager = MemoryManager()
    episodic = EpisodicMemory()
    semantic = SemanticKnowledge()
    skills = SkillMemory()
    
    # Store some memories
    print("[Memory] Storing experiences...")
    await manager.store("User asked about machine learning", tier='working', importance=0.8)
    await manager.store("Explained neural networks structure", tier='episodic', importance=0.7)
    await manager.store("ML is subset of AI", tier='semantic', importance=0.9)
    
    # Add semantic knowledge
    print("[Semantic] Adding knowledge relationships...")
    await semantic.add_fact("Machine Learning", "is_a", "AI")
    await semantic.add_fact("Neural Network", "is_a", "Machine Learning")
    await semantic.add_fact("Transformer", "is_a", "Neural Network")
    
    # Record episode
    print("[Episodes] Recording conversation...")
    await episodic.record_episode(
        query="Explain machine learning",
        reasoning_trace="Step 1: Define ML\nStep 2: Provide examples",
        result="Machine Learning is...",
        metrics={'time_ms': 1500, 'confidence': 0.95}
    )
    
    # Learn skills
    print("[Skills] Recording skill acquisition...")
    await skills.learn_skill("machine_learning_explanation", "education", "Explain ML concepts")
    await skills.use_skill("machine_learning_explanation", 50)
    await skills.use_skill("machine_learning_explanation", 30)
    
    # Retrieve memories
    print("\n[Retrieval] Finding memories about machine learning...")
    results = await manager.retrieve("machine learning", max_results=5)
    for mem in results:
        print(f"  - {mem.tier:15} (importance: {mem.importance:.2f}) {mem.content[:50]}...")
    
    # Get stats
    print("\n[Stats] Memory system status:")
    stats = await manager.get_statistics()
    print(f"  Total memories: {stats['total_memories']}")
    for tier, info in stats['by_tier'].items():
        print(f"    {tier:15}: {info['count']:5d}/{info['capacity']:5d} ({info['utilization']})")
    
    # Show related knowledge
    print("\n[Knowledge Graph] Entities related to 'Machine Learning':")
    related = await semantic.find_related("Machine Learning", max_depth=2)
    for entity in related[:5]:
        print(f"    - {entity}")
    
    # Show skills
    print("\n[Skills] Top learned skills:")
    top_skills = await skills.get_top_skills(5)
    for skill in top_skills:
        print(f"    - {skill['name']}: Level {skill['level']} (Mastery: {skill['mastery']:.1%})")


if __name__ == "__main__":
    asyncio.run(demo_memory_system())
