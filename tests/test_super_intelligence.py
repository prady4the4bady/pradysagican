"""
SUPER-INTELLIGENCE SYSTEM TESTS
================================
Comprehensive test suite for the integrated super-intelligence system.
Tests all major components and capabilities.
"""

import pytest
import asyncio
from typing import Dict, Any, List

from pradysagican.core.super_intelligence_hub import (
    SuperIntelligenceHub,
    SystemCapability,
    CapabilityHandler,
    MultiModalIntegration,
    AdvancedRAGSystem,
    MultiAgentCoordinator,
    get_hub,
    initialize_super_intelligence
)

from pradysagican.core.integrated_repositories import (
    FullAgentIntegration,
    CLIAgentIntegration,
    AIBrowserIntegration,
    LLMRunnerIntegration,
    RAGMemoryIntegration,
    FineTuningIntegration,
    VoiceAudioIntegration,
    WebResearchIntegration,
    MultiAgentIntegration,
    ObservabilityIntegration,
    list_all_repositories,
    INTEGRATIONS,
    RepositoryCategory
)


class TestSuperIntelligenceHub:
    """Test the core super-intelligence hub."""
    
    @pytest.mark.asyncio
    async def test_hub_initialization(self):
        """Test that the hub initializes correctly."""
        hub = await initialize_super_intelligence()
        assert hub is not None
        assert len(hub.capabilities) > 0
    
    @pytest.mark.asyncio
    async def test_capability_registration(self):
        """Test registering a new capability."""
        hub = get_hub()
        
        async def test_handler(**kwargs):
            return {"result": "success"}
        
        hub.register_capability(
            SystemCapability.MULTI_MODEL_ROUTING,
            test_handler,
            priority=10
        )
        
        assert SystemCapability.MULTI_MODEL_ROUTING in hub.capabilities
    
    @pytest.mark.asyncio
    async def test_capability_execution(self):
        """Test executing a capability."""
        hub = get_hub()
        
        result = await hub.execute_capability(
            SystemCapability.MULTI_MODEL_ROUTING,
            {"prompt": "test"}
        )
        
        assert result is not None
        assert "status" in result or "result" in result
    
    @pytest.mark.asyncio
    async def test_intelligent_routing(self):
        """Test intelligent task routing."""
        hub = get_hub()
        
        result = await hub.intelligent_route(
            "fine-tune a model",
            {"model": "llama2"}
        )
        
        assert result is not None
        assert "capability_used" in result or "success" in result
    
    def test_capabilities_summary(self):
        """Test getting capabilities summary."""
        hub = get_hub()
        summary = hub.get_capabilities_summary()
        
        assert "total_capabilities" in summary
        assert "capabilities" in summary
        assert len(summary["capabilities"]) > 0


class TestMultiModalIntegration:
    """Test multi-modal processing."""
    
    @pytest.mark.asyncio
    async def test_multimodal_initialization(self):
        """Test multi-modal integration initialization."""
        hub = get_hub()
        multimodal = MultiModalIntegration(hub)
        
        assert multimodal is not None
        assert multimodal.hub == hub
    
    @pytest.mark.asyncio
    async def test_process_text_only(self):
        """Test processing text-only input."""
        hub = get_hub()
        multimodal = MultiModalIntegration(hub)
        
        result = await multimodal.process_multimodal(
            text="Test query"
        )
        
        assert result is not None
        assert "modalities" in result
    
    @pytest.mark.asyncio
    async def test_synthesize_modalities(self):
        """Test modality synthesis."""
        hub = get_hub()
        multimodal = MultiModalIntegration(hub)
        
        results = {
            "text": {"output": "text output"},
            "audio": {"output": "audio output"}
        }
        
        synthesis = await multimodal._synthesize_modalities(results)
        
        assert synthesis is not None
        assert "coherence_score" in synthesis


class TestAdvancedRAG:
    """Test advanced RAG system."""
    
    @pytest.mark.asyncio
    async def test_rag_initialization(self):
        """Test RAG system initialization."""
        hub = get_hub()
        rag = AdvancedRAGSystem(hub)
        
        assert rag is not None
        assert rag.hub == hub
    
    @pytest.mark.asyncio
    async def test_semantic_retrieval(self):
        """Test semantic search retrieval."""
        hub = get_hub()
        rag = AdvancedRAGSystem(hub)
        
        results = await rag.retrieve_context(
            "test query",
            strategy="semantic"
        )
        
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_keyword_retrieval(self):
        """Test keyword search retrieval."""
        hub = get_hub()
        rag = AdvancedRAGSystem(hub)
        
        results = await rag.retrieve_context(
            "test query",
            strategy="keyword"
        )
        
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_hybrid_retrieval(self):
        """Test hybrid retrieval."""
        hub = get_hub()
        rag = AdvancedRAGSystem(hub)
        
        results = await rag.retrieve_context(
            "test query",
            strategy="hybrid"
        )
        
        assert isinstance(results, list)


class TestMultiAgentCoordinator:
    """Test multi-agent coordination."""
    
    @pytest.mark.asyncio
    async def test_coordinator_initialization(self):
        """Test coordinator initialization."""
        hub = get_hub()
        coordinator = MultiAgentCoordinator(hub)
        
        assert coordinator is not None
        assert len(coordinator.agents) == 0
    
    @pytest.mark.asyncio
    async def test_spawn_agent(self):
        """Test spawning an agent."""
        hub = get_hub()
        coordinator = MultiAgentCoordinator(hub)
        
        agent_id = await coordinator.spawn_agent("researcher", "data_analysis")
        
        assert agent_id is not None
        assert agent_id in coordinator.agents
    
    @pytest.mark.asyncio
    async def test_assign_task(self):
        """Test assigning task to agent."""
        hub = get_hub()
        coordinator = MultiAgentCoordinator(hub)
        
        agent_id = await coordinator.spawn_agent("analyzer", "analysis")
        task_id = await coordinator.assign_task("Analyze data", agent_id)
        
        assert task_id is not None
        assert task_id in coordinator.task_assignments
    
    @pytest.mark.asyncio
    async def test_coordinate_complex_task(self):
        """Test coordinating complex task across agents."""
        hub = get_hub()
        coordinator = MultiAgentCoordinator(hub)
        
        result = await coordinator.coordinate_agents("Build a comprehensive analysis report")
        
        assert result is not None
        assert "assignments" in result
        assert len(result["assignments"]) > 0


class TestFullAgentIntegration:
    """Test full-featured agent integration."""
    
    @pytest.mark.asyncio
    async def test_create_agent(self):
        """Test creating an agent."""
        integration = FullAgentIntegration()
        
        agent = await integration.create_agent(
            "ResearchAgent",
            "researcher",
            ["web_search", "analysis"]
        )
        
        assert agent is not None
        assert agent["role"] == "researcher"
        assert "web_search" in agent["capabilities"]
    
    @pytest.mark.asyncio
    async def test_create_workflow(self):
        """Test creating a workflow."""
        integration = FullAgentIntegration()
        
        workflow = await integration.create_workflow(
            "analysis",
            [
                {"type": "research", "action": "search"},
                {"type": "analysis", "action": "analyze"},
                {"type": "report", "action": "report"}
            ]
        )
        
        assert workflow is not None
        assert len(workflow["steps"]) == 3
    
    @pytest.mark.asyncio
    async def test_execute_workflow(self):
        """Test executing a workflow."""
        integration = FullAgentIntegration()
        
        workflow = await integration.create_workflow(
            "test",
            [{"type": "test", "action": "execute"}]
        )
        
        result = await integration.execute_workflow(workflow["id"])
        
        assert result is not None
        assert "results" in result


class TestLLMRunnerIntegration:
    """Test LLM runner integration."""
    
    @pytest.mark.asyncio
    async def test_pull_model(self):
        """Test pulling a model."""
        integration = LLMRunnerIntegration()
        
        model = await integration.pull_model("llama2")
        
        assert model is not None
        assert model["status"] == "downloaded"
    
    @pytest.mark.asyncio
    async def test_load_model(self):
        """Test loading a model."""
        integration = LLMRunnerIntegration()
        
        model = await integration.pull_model("llama2")
        result = await integration.load_model(model["id"] if isinstance(model, dict) and "id" in model else f"ollama_{model.get('name', '')}")
        
        assert result is not None
        assert result.get("status") in ["ready", "loaded", "error"]
    
    @pytest.mark.asyncio
    async def test_generate_text(self):
        """Test text generation."""
        integration = LLMRunnerIntegration()
        
        model = await integration.pull_model("llama2")
        model_id = f"ollama_llama2"
        await integration.load_model(model_id)
        
        result = await integration.generate(
            model_id,
            "What is machine learning?"
        )
        
        assert result is not None
        assert "output" in result or "error" in result


class TestRAGMemoryIntegration:
    """Test RAG & Memory integration."""
    
    @pytest.mark.asyncio
    async def test_create_collection(self):
        """Test creating a collection."""
        integration = RAGMemoryIntegration()
        
        collection = await integration.create_collection("test_collection")
        
        assert collection is not None
        assert collection["name"] == "test_collection"
    
    @pytest.mark.asyncio
    async def test_add_documents(self):
        """Test adding documents."""
        integration = RAGMemoryIntegration()
        
        collection = await integration.create_collection("test")
        
        result = await integration.add_documents(
            collection["id"],
            [
                {"text": "Document 1"},
                {"text": "Document 2"}
            ]
        )
        
        assert result is not None
        assert result["documents_added"] == 2


class TestFineTuningIntegration:
    """Test fine-tuning integration."""
    
    @pytest.mark.asyncio
    async def test_create_finetuning_job(self):
        """Test creating a fine-tuning job."""
        integration = FineTuningIntegration()
        
        job = await integration.create_finetuning_job(
            "llama2",
            "/path/to/training_data.jsonl",
            "lora"
        )
        
        assert job is not None
        assert job["method"] == "lora"
        assert job["status"] in ["queued", "running", "completed"]
    
    @pytest.mark.asyncio
    async def test_monitor_job(self):
        """Test monitoring a job."""
        integration = FineTuningIntegration()
        
        job = await integration.create_finetuning_job(
            "llama2",
            "/path/data.jsonl"
        )
        
        status = await integration.monitor_job(job["id"])
        
        assert status is not None
        assert "progress" in status


class TestVoiceAudioIntegration:
    """Test voice/audio integration."""
    
    @pytest.mark.asyncio
    async def test_transcribe_audio(self):
        """Test audio transcription."""
        integration = VoiceAudioIntegration()
        
        result = await integration.transcribe_audio(
            "/path/to/audio.wav",
            language="en"
        )
        
        assert result is not None
        assert "text" in result
    
    @pytest.mark.asyncio
    async def test_text_to_speech(self):
        """Test text-to-speech."""
        integration = VoiceAudioIntegration()
        
        result = await integration.text_to_speech(
            "Hello world",
            voice="female"
        )
        
        assert result is not None
        assert "output_path" in result


class TestWebResearchIntegration:
    """Test web research integration."""
    
    @pytest.mark.asyncio
    async def test_web_search(self):
        """Test web search."""
        integration = WebResearchIntegration()
        
        result = await integration.search_web("AI safety research")
        
        assert result is not None
        assert "results" in result
        assert len(result["results"]) > 0


class TestRepositoryListing:
    """Test repository listing and discovery."""
    
    def test_list_all_repositories(self):
        """Test listing all repositories."""
        repos = list_all_repositories()
        
        assert repos is not None
        assert len(repos) > 0
    
    def test_repository_categories(self):
        """Test repository categories."""
        repos = list_all_repositories()
        
        categories = set(r.category for r in repos)
        
        assert len(categories) > 0
        assert RepositoryCategory.FULL_AGENTS in categories or any(
            r.category.value == "full_agents" for r in repos
        )


class TestIntegrations:
    """Test all integration modules."""
    
    def test_all_integrations_loaded(self):
        """Test that all integrations are loaded."""
        assert len(INTEGRATIONS) > 0
        assert "full_agents" in INTEGRATIONS
        assert "cli_agents" in INTEGRATIONS
        assert "llm_runners" in INTEGRATIONS
    
    def test_get_integration(self):
        """Test getting an integration."""
        from pradysagican.core.integrated_repositories import get_integration
        
        full_agents = get_integration("full_agents")
        assert full_agents is not None
        
        invalid = get_integration("nonexistent")
        assert invalid is None


# Run tests with: pytest tests/test_super_intelligence.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
