"""
LAYER 3+ ENHANCEMENT: Knowledge Graph & RAG Pipeline
====================================================

Entity extraction, relationship graphs, semantic search,
and retrieval-augmented generation (RAG).

Attribution: Knowledge graph patterns (DBpedia, YAGO),
RAG patterns (LangChain, LlamaIndex)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Set, Tuple
from enum import Enum
import json

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════════
# ENTITY & RELATIONSHIP SYSTEM
# ════════════════════════════════════════════════════════════════════════════

class EntityType(str, Enum):
    """Entity types"""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    CONCEPT = "concept"
    TECHNOLOGY = "technology"
    ALGORITHM = "algorithm"
    METHOD = "method"
    TOOL = "tool"
    FRAMEWORK = "framework"
    DATASET = "dataset"


class RelationType(str, Enum):
    """Relationship types"""
    IS_A = "is_a"
    PART_OF = "part_of"
    USES = "uses"
    CREATES = "creates"
    SIMILAR_TO = "similar_to"
    OPPOSITE_OF = "opposite_of"
    REQUIRES = "requires"
    ENABLES = "enables"
    RELATES_TO = "relates_to"
    DEVELOPED_BY = "developed_by"


@dataclass
class Entity:
    """Knowledge graph entity"""
    id: str
    name: str
    entity_type: EntityType
    description: str
    properties: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0


@dataclass
class Relationship:
    """Connection between entities"""
    source_id: str
    target_id: str
    relation_type: RelationType
    strength: float = 0.5
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


# ════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE GRAPH
# ════════════════════════════════════════════════════════════════════════════

class KnowledgeGraph:
    """
    Complete knowledge graph for semantic search and reasoning
    """
    
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.relationships: List[Relationship] = []
        self.entity_index: Dict[str, Set[str]] = {}  # Full text index
        self.relationship_index: Dict[str, List[Relationship]] = {}  # By source
    
    async def add_entity(self, entity_id: str, name: str, 
                        entity_type: EntityType, description: str,
                        properties: Dict = None) -> Entity:
        """Add entity to graph"""
        entity = Entity(
            id=entity_id,
            name=name,
            entity_type=entity_type,
            description=description,
            properties=properties or {}
        )
        
        self.entities[entity_id] = entity
        
        # Index for full text search
        text = f"{name} {description}".lower()
        for word in text.split():
            if word not in self.entity_index:
                self.entity_index[word] = set()
            self.entity_index[word].add(entity_id)
        
        logger.info(f"Added entity: {name} ({entity_type.value})")
        return entity
    
    async def add_relationship(self, source_id: str, target_id: str,
                              relation_type: RelationType,
                              strength: float = 0.5) -> Relationship:
        """Add relationship between entities"""
        if source_id not in self.entities or target_id not in self.entities:
            return None
        
        rel = Relationship(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength
        )
        
        self.relationships.append(rel)
        
        # Index by source
        if source_id not in self.relationship_index:
            self.relationship_index[source_id] = []
        self.relationship_index[source_id].append(rel)
        
        logger.info(f"Added relationship: {source_id} -{relation_type.value}-> {target_id}")
        return rel
    
    async def search_entities(self, query: str, limit: int = 10) -> List[Entity]:
        """Search entities by text"""
        query_words = query.lower().split()
        matches: Dict[str, int] = {}
        
        for word in query_words:
            if word in self.entity_index:
                for entity_id in self.entity_index[word]:
                    matches[entity_id] = matches.get(entity_id, 0) + 1
        
        # Sort by relevance
        sorted_matches = sorted(
            matches.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            self.entities[entity_id]
            for entity_id, _ in sorted_matches[:limit]
            if entity_id in self.entities
        ]
    
    async def get_entity_context(self, entity_id: str, 
                                 depth: int = 2) -> Dict[str, Any]:
        """Get full context around entity"""
        if entity_id not in self.entities:
            return None
        
        entity = self.entities[entity_id]
        context = {
            'entity': {
                'id': entity.id,
                'name': entity.name,
                'type': entity.entity_type.value,
                'description': entity.description,
            },
            'related': []
        }
        
        # Get related entities
        if entity_id in self.relationship_index:
            for rel in self.relationship_index[entity_id][:5]:  # Top 5
                target = self.entities.get(rel.target_id)
                if target:
                    context['related'].append({
                        'entity_name': target.name,
                        'relation_type': rel.relation_type.value,
                        'strength': rel.strength,
                    })
        
        return context
    
    async def find_paths(self, source_id: str, target_id: str,
                        max_depth: int = 3) -> List[List[str]]:
        """Find paths between entities (BFS)"""
        paths = []
        visited = set()
        
        def bfs(current_id: str, target_id: str, path: List[str], depth: int):
            if depth == 0 or current_id in visited:
                return
            
            visited.add(current_id)
            
            if current_id == target_id:
                paths.append(path + [current_id])
                visited.remove(current_id)
                return
            
            # Find connected entities
            if current_id in self.relationship_index:
                for rel in self.relationship_index[current_id]:
                    bfs(rel.target_id, target_id, path + [current_id], depth - 1)
            
            visited.remove(current_id)
        
        bfs(source_id, target_id, [], max_depth)
        return paths
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics"""
        entity_types = {}
        for entity in self.entities.values():
            etype = entity.entity_type.value
            entity_types[etype] = entity_types.get(etype, 0) + 1
        
        rel_types = {}
        for rel in self.relationships:
            rtype = rel.relation_type.value
            rel_types[rtype] = rel_types.get(rtype, 0) + 1
        
        return {
            'total_entities': len(self.entities),
            'total_relationships': len(self.relationships),
            'entities_by_type': entity_types,
            'relationships_by_type': rel_types,
            'average_connections': len(self.relationships) / max(len(self.entities), 1)
        }


# ════════════════════════════════════════════════════════════════════════════
# RETRIEVAL-AUGMENTED GENERATION (RAG)
# ════════════════════════════════════════════════════════════════════════════

class RAGPipeline:
    """
    RAG pipeline: Retrieve relevant context, then generate response
    """
    
    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.kg = knowledge_graph
        self.documents: Dict[str, str] = {}  # Document store
        self.doc_counter = 0
    
    async def add_document(self, content: str, metadata: Dict = None) -> str:
        """Add document to RAG"""
        doc_id = f"doc_{self.doc_counter}"
        self.doc_counter += 1
        
        self.documents[doc_id] = {
            'content': content,
            'metadata': metadata or {},
            'created_at': datetime.now().isoformat()
        }
        
        # Extract entities from document
        await self._extract_entities(doc_id, content)
        
        return doc_id
    
    async def _extract_entities(self, doc_id: str, content: str):
        """Extract entities from document (simplified)"""
        # In production, use NER model
        words = content.split()
        for word in words[:20]:  # First 20 words
            if len(word) > 5:  # Skip short words
                await self.kg.add_entity(
                    entity_id=f"{doc_id}_{word}",
                    name=word,
                    entity_type=EntityType.CONCEPT,
                    description=f"Mentioned in {doc_id}"
                )
    
    async def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for query"""
        # Search entities
        entities = await self.kg.search_entities(query, limit=top_k)
        
        results = []
        for entity in entities:
            context = await self.kg.get_entity_context(entity.id)
            results.append(context)
        
        return results
    
    async def generate_with_context(self, query: str, 
                                    llm_generator) -> str:
        """Generate response using retrieved context"""
        # Retrieve
        context = await self.retrieve(query, top_k=3)
        
        # Format context
        context_str = "\n".join([
            f"- {c['entity']['name']}: {c['entity']['description']}"
            for c in context
        ])
        
        # Generate with context
        prompt = f"""
Query: {query}

Relevant Context:
{context_str}

Based on the above context, provide a comprehensive answer:
"""
        
        response = await llm_generator(prompt)
        return response


# ════════════════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════════════════

async def demo_knowledge_graph():
    """Demonstrate knowledge graph and RAG"""
    print("\n" + "="*70)
    print("KNOWLEDGE GRAPH & RAG PIPELINE DEMO")
    print("="*70 + "\n")
    
    kg = KnowledgeGraph()
    
    # Add entities
    print("[Graph] Adding entities...")
    
    entities = [
        ("ml", "Machine Learning", EntityType.TECHNOLOGY, "Learn from data"),
        ("dl", "Deep Learning", EntityType.TECHNOLOGY, "Neural networks"),
        ("nn", "Neural Network", EntityType.ALGORITHM, "Brain-inspired model"),
        ("nlp", "NLP", EntityType.TECHNOLOGY, "Text processing"),
        ("cv", "Computer Vision", EntityType.TECHNOLOGY, "Image processing"),
        ("bert", "BERT", EntityType.ALGORITHM, "Language model"),
        ("transformer", "Transformer", EntityType.ALGORITHM, "Attention mechanism"),
    ]
    
    for ent_id, name, ent_type, desc in entities:
        await kg.add_entity(ent_id, name, ent_type, desc)
    
    # Add relationships
    print("\n[Graph] Adding relationships...")
    
    relationships = [
        ("ml", "dl", RelationType.IS_A),
        ("dl", "nn", RelationType.USES),
        ("nlp", "transformer", RelationType.USES),
        ("cv", "transformer", RelationType.USES),
        ("bert", "nlp", RelationType.PART_OF),
        ("bert", "transformer", RelationType.USES),
    ]
    
    for src, tgt, rel in relationships:
        await kg.add_relationship(src, tgt, rel)
    
    # Search
    print("\n[Search] Searching for 'machine learning'...")
    results = await kg.search_entities("machine learning")
    for entity in results[:3]:
        print(f"  - {entity.name} ({entity.entity_type.value})")
    
    # Get context
    print("\n[Context] Getting context for 'Deep Learning'...")
    context = await kg.get_entity_context("dl")
    if context:
        print(f"  Entity: {context['entity']['name']}")
        print(f"  Related concepts:")
        for rel in context['related'][:3]:
            print(f"    - {rel['entity_name']} ({rel['relation_type']})")
    
    # Find paths
    print("\n[Paths] Finding path from ML to NLP...")
    paths = await kg.find_paths("ml", "nlp", max_depth=3)
    if paths:
        for path in paths[:3]:
            path_names = [kg.entities[p].name if p in kg.entities else p for p in path]
            print(f"  -> {' -> '.join(path_names)}")
    
    # Statistics
    print("\n[Stats] Knowledge graph statistics:")
    stats = await kg.get_statistics()
    print(f"  Entities: {stats['total_entities']}")
    print(f"  Relationships: {stats['total_relationships']}")
    print(f"  Avg connections: {stats['average_connections']:.1f}")
    
    # RAG Pipeline
    print("\n[RAG] Testing RAG pipeline...")
    rag = RAGPipeline(kg)
    
    doc = """
    Machine Learning is a subset of AI that enables computers to learn from data.
    Deep Learning uses neural networks with multiple layers.
    Transformers use attention mechanisms for NLP tasks.
    BERT is a transformer-based language model.
    """
    
    doc_id = await rag.add_document(doc, {"source": "demo"})
    print(f"  Added document: {doc_id}")
    
    print("\n[RAG] Retrieving context for 'neural networks'...")
    context = await rag.retrieve("neural networks", top_k=3)
    print(f"  Found {len(context)} relevant entities")


if __name__ == "__main__":
    asyncio.run(demo_knowledge_graph())
