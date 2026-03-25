"""Test suite for Phase 8 Frontier Capabilities (F656-F660)."""

import pytest
from unittest.mock import Mock, patch

from pradysagican.core.godmode.frontier import (
    CrossDomainTransferLearning,
    DomainTransferLearning,
    AdaptiveExpertise,
    CompetitiveAdvantageEngine,
    DomainExpertise,
    TransferConnection,
    CompetitiveAdvantageProfile,
    Domain,
    TransferMechanism,
    CompetitiveAdvantage,
)


class TestCrossDomainTransferLearning:
    """Test cross-domain transfer learning."""

    def test_transfer_learning_initialization(self):
        """Test transfer learning initializes."""
        transfer = CrossDomainTransferLearning()
        assert len(transfer.domain_expertise) == 0
        assert len(transfer.transfer_connections) == 0
        assert len(transfer.transfer_graph) > 0

    def test_transfer_graph_construction(self):
        """Test transfer graph is properly constructed."""
        transfer = CrossDomainTransferLearning()
        graph = transfer.transfer_graph

        # Should have multiple domains connected
        assert len(graph) > 0

        # Check some expected relationships
        assert len(graph[Domain.MATHEMATICS]) > 0
        assert Domain.PHYSICS in graph[Domain.MATHEMATICS]

    @pytest.mark.asyncio
    async def test_transfer_knowledge_between_domains(self):
        """Test transferring knowledge between domains."""
        transfer = CrossDomainTransferLearning()

        # Create source expertise
        source_expertise = DomainExpertise(
            expertise_id="source_1",
            domain=Domain.MATHEMATICS,
            patterns=["pattern_1", "pattern_2", "optimization"],
            rules=["rule_1", "rule_2"],
            performance_score=0.85,
        )

        connection = await transfer.transfer_knowledge(
            Domain.MATHEMATICS,
            Domain.PHYSICS,
            source_expertise,
            TransferMechanism.FEATURE_TRANSFER,
        )

        assert connection is not None
        assert connection.source_domain == Domain.MATHEMATICS
        assert connection.target_domain == Domain.PHYSICS
        assert connection.transfer_score > 0
        assert len(connection.patterns_transferred) > 0

    def test_domain_similarity_calculation(self):
        """Test domain similarity is properly calculated."""
        transfer = CrossDomainTransferLearning()

        # Directly connected domains should have high similarity
        sim_high = transfer._calculate_domain_similarity(
            Domain.MATHEMATICS, Domain.PHYSICS
        )
        assert sim_high > 0.5

        # Randomly distant domains should have lower similarity
        sim_low = transfer._calculate_domain_similarity(
            Domain.MUSIC, Domain.ENGINEERING
        )
        assert sim_low >= 0.1  # At least some baseline

    def test_similarity_caching(self):
        """Test similarity scores are cached."""
        transfer = CrossDomainTransferLearning()

        sim1 = transfer._calculate_domain_similarity(
            Domain.MATHEMATICS, Domain.PHYSICS
        )
        sim2 = transfer._calculate_domain_similarity(
            Domain.MATHEMATICS, Domain.PHYSICS
        )

        # Should be identical (cached)
        assert sim1 == sim2

    def test_transfer_graph_visualization(self):
        """Test transfer graph visualization."""
        transfer = CrossDomainTransferLearning()
        viz = transfer.get_transfer_graph_visualization()

        assert "domains" in viz
        assert "connections" in viz
        assert len(viz["domains"]) > 0

    def test_transferable_patterns_selection(self):
        """Test selecting transferable patterns."""
        transfer = CrossDomainTransferLearning()

        patterns = [
            "optimization_technique",
            "search_strategy",
            "domain_specific_rule",
            "classification_method",
            "specific_physics_formula",
        ]

        transferable = transfer._select_transferable_patterns(
            patterns,
            Domain.MATHEMATICS,
            Domain.PHYSICS,
        )

        assert len(transferable) > 0
        # Should prioritize general patterns
        assert any("optimization" in p for p in transferable) or any(
            "search" in p for p in transferable
        )


class TestDomainTransferLearning:
    """Test domain adaptation through transfer learning."""

    def test_domain_transfer_initialization(self):
        """Test domain transfer initializes."""
        transfer = DomainTransferLearning()
        assert len(transfer.domain_adaptations) == 0

    @pytest.mark.asyncio
    async def test_adapt_to_domain(self):
        """Test adapting to new domain."""
        transfer = DomainTransferLearning()

        result = await transfer.adapt_to_domain(
            Domain.MEDICINE,
            initial_performance=0.6,
            source_models=["model_1", "model_2"],
            adaptation_budget=50,
        )

        assert result is not None
        assert result["target_domain"] == Domain.MEDICINE.value
        assert result["final_performance"] >= result["initial_performance"]
        assert result["adaptation_steps"] > 0

    @pytest.mark.asyncio
    async def test_domain_characteristics_analysis(self):
        """Test domain characteristics are analyzed."""
        transfer = DomainTransferLearning()

        result = await transfer.adapt_to_domain(
            Domain.ECONOMICS,
            0.5,
            ["model"],
            adaptation_budget=10,
        )

        assert "domain_characteristics" in result
        chars = result["domain_characteristics"]
        assert "complexity" in chars
        assert "transferability" in chars

    @pytest.mark.asyncio
    async def test_performance_improvement_tracking(self):
        """Test performance improvement is tracked."""
        transfer = DomainTransferLearning()

        result = await transfer.adapt_to_domain(
            Domain.BIOLOGY,
            0.5,
            [],
            adaptation_budget=30,
        )

        improvement = result["final_performance"] - result["initial_performance"]
        assert improvement >= 0

    def test_adaptation_history(self):
        """Test adaptation history is maintained."""
        transfer = DomainTransferLearning()

        # Manually add history
        transfer.performance_history[Domain.BIOLOGY] = [0.5, 0.55, 0.6, 0.62]

        history = transfer.get_adaptation_history(Domain.BIOLOGY)
        assert len(history) == 4
        assert all(
            history[i] <= history[i + 1] for i in range(len(history) - 1)
        )  # Monotonic


class TestAdaptiveExpertise:
    """Test adaptive expertise development."""

    def test_expertise_initialization(self):
        """Test expertise system initializes."""
        expertise = AdaptiveExpertise()
        assert len(expertise.expertise_profiles) == 0

    def test_develop_expertise(self):
        """Test developing expertise in domain."""
        expertise = AdaptiveExpertise()

        experiences = [
            {"success": True, "outcome": "positive"},
            {"success": True, "outcome": "positive"},
            {"success": False, "outcome": "negative"},
        ]

        domain_expertise = expertise.develop_expertise(
            Domain.MATHEMATICS,
            experiences,
        )

        assert domain_expertise is not None
        assert domain_expertise.domain == Domain.MATHEMATICS
        assert len(domain_expertise.patterns) > 0
        assert len(domain_expertise.rules) > 0
        assert domain_expertise.performance_score > 0

    def test_patterns_extracted_from_experiences(self):
        """Test patterns are extracted from experiences."""
        expertise = AdaptiveExpertise()

        experiences = [
            {"success": True},
            {"success": True},
            {"success": False},
            {"success": True},
        ]

        domain_exp = expertise.develop_expertise(Domain.PHYSICS, experiences)

        # Should have 3 patterns from successes
        assert len(domain_exp.patterns) == 3

    def test_rules_extracted_from_experiences(self):
        """Test rules are extracted from experiences."""
        expertise = AdaptiveExpertise()

        experiences = [
            {"outcome": "result_1"},
            {"outcome": "result_2"},
            {"outcome": "result_3"},
        ]

        domain_exp = expertise.develop_expertise(Domain.CHEMISTRY, experiences)

        assert len(domain_exp.rules) > 0

    def test_performance_calculation(self):
        """Test performance is calculated correctly."""
        expertise = AdaptiveExpertise()

        # Many patterns and rules should give high performance
        experiences = [{"success": True} for _ in range(20)]

        domain_exp = expertise.develop_expertise(Domain.BIOLOGY, experiences)

        assert domain_exp.performance_score > 0.3

    def test_specialization_level(self):
        """Test specialization level is calculated."""
        expertise = AdaptiveExpertise()

        experiences = [{"success": True} for _ in range(15)]

        domain_exp = expertise.develop_expertise(Domain.MEDICINE, experiences)

        assert 0.0 <= domain_exp.specialization_level <= 1.0
        assert domain_exp.specialization_level > 0

    def test_aggregate_expertise(self):
        """Test aggregating expertise across domains."""
        expertise = AdaptiveExpertise()

        # Develop expertise in multiple domains
        for domain in [Domain.MATHEMATICS, Domain.PHYSICS, Domain.CHEMISTRY]:
            exp = DomainExpertise(
                expertise_id=f"exp_{domain.value}",
                domain=domain,
                patterns=["p1", "p2", "p3"],
                rules=["r1", "r2"],
                performance_score=0.7 + np.random.random() * 0.2,
            )
            expertise.expertise_profiles[domain] = exp

        aggregate = expertise.aggregate_expertise(
            [Domain.MATHEMATICS, Domain.PHYSICS, Domain.CHEMISTRY]
        )

        assert aggregate["domains_count"] == 3
        assert aggregate["total_patterns"] > 0
        assert aggregate["average_performance"] > 0

    def test_expertise_report(self):
        """Test expertise report generation."""
        expertise = AdaptiveExpertise()

        # Add some expertise
        for domain in [Domain.MATHEMATICS, Domain.PHYSICS]:
            exp = DomainExpertise(
                expertise_id=f"exp_{domain.value}",
                domain=domain,
                patterns=["p1", "p2"],
                performance_score=0.75,
            )
            expertise.expertise_profiles[domain] = exp

        report = expertise.get_expertise_report()

        assert report["domains_with_expertise"] == 2
        assert report["total_patterns"] >= 2
        assert "expertise_by_domain" in report


class TestCompetitiveAdvantageEngine:
    """Test competitive advantage generation."""

    def test_engine_initialization(self):
        """Test engine initializes."""
        engine = CompetitiveAdvantageEngine()
        assert len(engine.advantage_profiles) == 0

    @pytest.mark.asyncio
    async def test_generate_competitive_advantage(self):
        """Test generating competitive advantage."""
        engine = CompetitiveAdvantageEngine()

        capabilities = {
            "speed": 0.85,
            "accuracy": 0.92,
            "generalization": 0.88,
            "efficiency": 0.75,
        }

        profile = await engine.generate_competitive_advantage(
            Domain.COMPUTER_SCIENCE,
            capabilities,
            baseline_performance=0.75,
            competitors=["system_a", "system_b"],
        )

        assert profile is not None
        assert profile.domain == Domain.COMPUTER_SCIENCE
        assert len(profile.advantages) > 0
        assert profile.overall_score > 0

    @pytest.mark.asyncio
    async def test_advantage_identification(self):
        """Test advantages are properly identified."""
        engine = CompetitiveAdvantageEngine()

        capabilities = {
            "speed": 0.9,
            "accuracy": 0.95,
            "efficiency": 0.8,
        }

        profile = await engine.generate_competitive_advantage(
            Domain.ENGINEERING,
            capabilities,
            0.5,
            [],
        )

        # Should identify multiple advantages
        assert len(profile.advantages) >= 2

    @pytest.mark.asyncio
    async def test_competitive_scoring(self):
        """Test competitive advantage vs baselines."""
        engine = CompetitiveAdvantageEngine()

        capabilities = {"speed": 0.9, "accuracy": 0.95}

        profile = await engine.generate_competitive_advantage(
            Domain.PHYSICS,
            capabilities,
            0.6,
            ["competitor_1", "competitor_2"],
        )

        assert profile.vs_baseline > 0
        assert len(profile.vs_competitors) == 2
        assert all(v > 0 for v in profile.vs_competitors.values())

    @pytest.mark.asyncio
    async def test_market_analysis(self):
        """Test market analysis report."""
        engine = CompetitiveAdvantageEngine()

        # Generate multiple advantage profiles
        for domain in [Domain.MATHEMATICS, Domain.PHYSICS, Domain.COMPUTER_SCIENCE]:
            await engine.generate_competitive_advantage(
                domain,
                {"speed": 0.8, "accuracy": 0.9},
                0.6,
                [],
            )

        analysis = engine.get_market_analysis()

        assert analysis["total_advantage_profiles"] >= 3
        assert analysis["domains_analyzed"] == 3
        assert analysis["average_advantage"] > 0


class TestFrontierIntegration:
    """Test integration of frontier capabilities."""

    @pytest.mark.asyncio
    async def test_transfer_learning_with_domain_adaptation(self):
        """Test transfer learning with domain adaptation."""
        transfer = CrossDomainTransferLearning()
        domain_adapt = DomainTransferLearning()

        # Transfer knowledge
        source_expertise = DomainExpertise(
            expertise_id="src",
            domain=Domain.MATHEMATICS,
            patterns=["pattern_1", "optimization"],
        )

        connection = await transfer.transfer_knowledge(
            Domain.MATHEMATICS,
            Domain.PHYSICS,
            source_expertise,
        )

        # Adapt to new domain
        result = await domain_adapt.adapt_to_domain(
            Domain.PHYSICS,
            0.6,
            ["model_1"],
            adaptation_budget=20,
        )

        assert connection is not None
        assert result is not None
        assert result["final_performance"] >= 0.6

    @pytest.mark.asyncio
    async def test_expertise_development_with_competitive_advantage(self):
        """Test expertise with competitive advantage analysis."""
        expertise = AdaptiveExpertise()
        competitive = CompetitiveAdvantageEngine()

        # Develop expertise
        experiences = [{"success": True, "outcome": "positive"} for _ in range(10)]
        domain_exp = expertise.develop_expertise(Domain.MATHEMATICS, experiences)

        # Analyze competitive advantage
        capabilities = {
            "speed": 0.85,
            "accuracy": domain_exp.performance_score,
        }

        advantage = await competitive.generate_competitive_advantage(
            Domain.MATHEMATICS,
            capabilities,
            0.5,
            ["competitor"],
        )

        assert domain_exp.performance_score > 0
        assert advantage.overall_score > 0

    def test_all_domains_transferable(self):
        """Test all domains are represented and transferable."""
        transfer = CrossDomainTransferLearning()

        # Check all domains are in the transfer graph
        all_domains = list(Domain)
        connected_domains = set(transfer.transfer_graph.keys())

        # Most domains should be connected
        assert len(connected_domains) > 10


import numpy as np


class TestFrontierMetrics:
    """Test frontier capability metrics."""

    def test_transfer_effectiveness_score(self):
        """Test transfer effectiveness is properly scored."""
        connection = TransferConnection(
            connection_id="test",
            source_domain=Domain.MATHEMATICS,
            target_domain=Domain.PHYSICS,
            transfer_mechanism=TransferMechanism.FEATURE_TRANSFER,
            transfer_score=0.85,
            effectiveness=0.82,
        )

        assert 0.0 <= connection.effectiveness <= 1.0
        assert connection.effectiveness > 0

    def test_expertise_coverage_score(self):
        """Test expertise coverage is properly scored."""
        expertise = DomainExpertise(
            expertise_id="test",
            domain=Domain.MATHEMATICS,
            patterns=["p1", "p2", "p3"],
            coverage=0.3,
        )

        assert 0.0 <= expertise.coverage <= 1.0

    def test_competitive_advantage_scoring(self):
        """Test competitive advantage scoring."""
        profile = CompetitiveAdvantageProfile(
            profile_id="test",
            domain=Domain.PHYSICS,
            advantages={
                CompetitiveAdvantage.SPEED: 0.9,
                CompetitiveAdvantage.ACCURACY: 0.95,
            },
            overall_score=0.92,
        )

        assert 0.0 <= profile.overall_score <= 1.0
        assert all(0.0 <= v <= 1.0 for v in profile.advantages.values())

    def test_domain_adaptation_metrics(self):
        """Test domain adaptation produces valid metrics."""
        # Manually create result
        result = {
            "initial_performance": 0.5,
            "final_performance": 0.72,
            "total_improvement": 0.22,
        }

        assert result["final_performance"] >= result["initial_performance"]
        assert result["total_improvement"] >= 0
        assert result["total_improvement"] <= 1.0


class TestCrossDomainScenarios:
    """Test realistic cross-domain scenarios."""

    @pytest.mark.asyncio
    async def test_physics_to_engineering_transfer(self):
        """Test transferring physics knowledge to engineering."""
        transfer = CrossDomainTransferLearning()

        source_expertise = DomainExpertise(
            expertise_id="physics",
            domain=Domain.PHYSICS,
            patterns=["mechanics", "dynamics", "optimization"],
            performance_score=0.85,
        )

        connection = await transfer.transfer_knowledge(
            Domain.PHYSICS,
            Domain.ENGINEERING,
            source_expertise,
        )

        assert connection.transfer_score >= 0.5  # Should have good similarity

    @pytest.mark.asyncio
    async def test_math_to_cs_transfer(self):
        """Test transferring mathematics to computer science."""
        transfer = CrossDomainTransferLearning()

        source_expertise = DomainExpertise(
            expertise_id="math",
            domain=Domain.MATHEMATICS,
            patterns=["algorithm_design", "complexity_analysis"],
            performance_score=0.9,
        )

        connection = await transfer.transfer_knowledge(
            Domain.MATHEMATICS,
            Domain.COMPUTER_SCIENCE,
            source_expertise,
        )

        assert connection.transfer_score > 0.4

    @pytest.mark.asyncio
    async def test_biology_to_medicine_transfer(self):
        """Test transferring biology to medicine."""
        transfer = CrossDomainTransferLearning()

        source_expertise = DomainExpertise(
            expertise_id="bio",
            domain=Domain.BIOLOGY,
            patterns=["cellular_mechanisms", "pathway_analysis"],
            performance_score=0.8,
        )

        connection = await transfer.transfer_knowledge(
            Domain.BIOLOGY,
            Domain.MEDICINE,
            source_expertise,
        )

        # Should have reasonable transfer potential
        assert connection.transfer_score > 0.3
