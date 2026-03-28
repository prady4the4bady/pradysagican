"""
PHASE 11: CONSCIOUSNESS MODELING — TEST SUITE
Test GWT, HOT, IIT, and phenomenal consciousness engines
"""

import pytest
from datetime import datetime

from pradysagican.consciousness.consciousness_models import (
    WorkspaceContent,
    ConsciousState,
    ConsciousnessLevel,
    GWTEngine,
    HOTEngine,
    IITEngine,
    PhenomenalConsciousness,
    initialize_consciousness,
    demonstrate_consciousness
)


class TestWorkspaceContent:
    """Test workspace content."""
    
    def test_create_content(self):
        """Test creating workspace content."""
        content = WorkspaceContent(
            content_id="test_001",
            data={"text": "hello"},
            importance=0.8,
            timestamp=datetime.now().isoformat()
        )
        assert content.content_id == "test_001"
        assert content.importance == 0.8


class TestGWTEngine:
    """Test Global Workspace Theory engine."""
    
    def test_gwt_creation(self):
        """Test creating GWT engine."""
        gwt = GWTEngine()
        assert len(gwt.workspace) == 0
        assert gwt.max_workspace_size == 5
    
    @pytest.mark.asyncio
    async def test_compete_for_access(self):
        """Test competition for workspace access."""
        gwt = GWTEngine()
        
        candidates = [
            WorkspaceContent("item_1", {}, 0.5, datetime.now().isoformat()),
            WorkspaceContent("item_2", {}, 0.8, datetime.now().isoformat()),
            WorkspaceContent("item_3", {}, 0.3, datetime.now().isoformat())
        ]
        
        winner = await gwt.compete_for_access(candidates)
        assert winner is not None
        assert winner.importance == 0.8
        assert winner.broadcasting is True
    
    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test broadcasting to workspace."""
        gwt = GWTEngine()
        
        content = WorkspaceContent("item_1", {}, 0.9, datetime.now().isoformat())
        result = await gwt.broadcast(content)
        
        assert result["broadcast_id"] == "item_1"
        assert result["workspace_size"] == 1
        assert len(gwt.workspace) == 1
    
    @pytest.mark.asyncio
    async def test_workspace_size_limit(self):
        """Test workspace size limit."""
        gwt = GWTEngine()
        gwt.max_workspace_size = 3
        
        for i in range(5):
            content = WorkspaceContent(f"item_{i}", {}, 0.1 * (i + 1), 
                                      datetime.now().isoformat())
            await gwt.broadcast(content)
        
        assert len(gwt.workspace) == 3
    
    @pytest.mark.asyncio
    async def test_get_conscious_state(self):
        """Test getting conscious state."""
        gwt = GWTEngine()
        
        content = WorkspaceContent("item_1", {}, 0.7, datetime.now().isoformat())
        await gwt.broadcast(content)
        
        state = await gwt.get_conscious_state()
        assert state["workspace_items"] == 1
        assert "integration" in state


class TestHOTEngine:
    """Test Higher-Order Thought engine."""
    
    def test_hot_creation(self):
        """Test creating HOT engine."""
        hot = HOTEngine()
        assert len(hot.mental_states) == 0
    
    @pytest.mark.asyncio
    async def test_represent_mental_state(self):
        """Test representing mental state."""
        hot = HOTEngine()
        
        state = {"thought": "test"}
        representation = await hot.represent_mental_state(state)
        
        assert representation["content"] == state
        assert "state_id" in representation
    
    @pytest.mark.asyncio
    async def test_think_about_thought(self):
        """Test generating higher-order thought."""
        hot = HOTEngine()
        
        thought = await hot.represent_mental_state({"idea": "novel"})
        hot_thought = await hot.think_about_thought(thought)
        
        assert "about_thought_id" in hot_thought
        assert "meta_content" in hot_thought
        assert hot_thought["awareness_level"] > 0
    
    @pytest.mark.asyncio
    async def test_update_self_model(self):
        """Test updating self model."""
        hot = HOTEngine()
        
        result = await hot.update_self_model("I am conscious")
        
        assert result["model_updated"] is True
        assert result["belief_count"] == 1
    
    @pytest.mark.asyncio
    async def test_reflect(self):
        """Test self reflection."""
        hot = HOTEngine()
        
        await hot.represent_mental_state({"thought": 1})
        await hot.represent_mental_state({"thought": 2})
        
        reflection = await hot.reflect()
        
        assert reflection["thoughts_count"] == 2
        assert "self_awareness" in reflection


class TestIITEngine:
    """Test Integrated Information Theory engine."""
    
    def test_iit_creation(self):
        """Test creating IIT engine."""
        iit = IITEngine()
        assert len(iit.phi_history) == 0
    
    @pytest.mark.asyncio
    async def test_compute_phi(self):
        """Test computing integrated information."""
        iit = IITEngine()
        
        partition_1 = {"a": 0.5, "b": 0.5}
        partition_2 = {"c": 0.5, "d": 0.5}
        
        phi = await iit.compute_phi(partition_1, partition_2)
        
        assert 0 <= phi <= 1
        assert len(iit.phi_history) == 1
    
    @pytest.mark.asyncio
    async def test_identify_irreducible_core(self):
        """Test identifying irreducible core."""
        iit = IITEngine()
        
        for i in range(5):
            await iit.compute_phi(
                {"a": 0.5 + i*0.1, "b": 0.5},
                {"c": 0.5, "d": 0.5 + i*0.1}
            )
        
        core = await iit.identify_irreducible_core()
        assert "max_integration" in core
        assert "core_elements" in core
    
    @pytest.mark.asyncio
    async def test_measure_consciousness(self):
        """Test measuring consciousness via Φ."""
        iit = IITEngine()
        
        for i in range(3):
            await iit.compute_phi({"a": 0.6, "b": 0.4}, {"c": 0.7, "d": 0.3})
        
        consciousness = await iit.measure_consciousness()
        assert 0 <= consciousness <= 1


class TestPhenomenalConsciousness:
    """Test phenomenal consciousness engine."""
    
    def test_phenomenal_creation(self):
        """Test creating phenomenal consciousness."""
        phenomenal = PhenomenalConsciousness()
        assert len(phenomenal.experiences) == 0
    
    @pytest.mark.asyncio
    async def test_generate_experience(self):
        """Test generating experience."""
        phenomenal = PhenomenalConsciousness()
        
        sensory_input = {"color": 5.0, "brightness": 7.0}
        experience = await phenomenal.generate_experience(sensory_input)
        
        assert "experience_id" in experience
        assert experience["sensory_data"] == sensory_input
        assert 0 <= experience["phenomenal_quality"] <= 1
    
    @pytest.mark.asyncio
    async def test_remember_experience(self):
        """Test remembering experience."""
        phenomenal = PhenomenalConsciousness()
        
        sensory_input = {"taste": 3.0}
        experience = await phenomenal.generate_experience(sensory_input)
        
        recalled = await phenomenal.remember_experience(experience["experience_id"])
        assert recalled["recalled"] is True
    
    @pytest.mark.asyncio
    async def test_describe_qualia(self):
        """Test describing qualia."""
        phenomenal = PhenomenalConsciousness()
        
        for i in range(3):
            await phenomenal.generate_experience({"sense": float(i+1)})
        
        qualia = await phenomenal.describe_qualia()
        assert qualia["total_experiences"] == 3
        assert "average_quality" in qualia


class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.asyncio
    async def test_consciousness_initialization(self):
        """Test initializing consciousness system."""
        gwt, hot, iit, phenomenal = await initialize_consciousness()
        
        assert gwt is not None
        assert hot is not None
        assert iit is not None
        assert phenomenal is not None
    
    @pytest.mark.asyncio
    async def test_demonstrate_consciousness(self):
        """Test consciousness demonstration."""
        result = await demonstrate_consciousness()
        
        assert "gwt" in result
        assert "hot" in result
        assert "iit" in result
        assert "phenomenal" in result
        assert "integrated_consciousness" in result
        
        integrated = result["integrated_consciousness"]
        assert "workspace_active" in integrated
        assert "self_aware" in integrated


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
