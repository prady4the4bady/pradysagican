"""Test suite for Phase 6 MAE Proposer module (F612)."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from pradysagican.core.co_evolution.proposer import (
    MAEProposer,
    Proposal,
    PopulationSnapshot,
    ProposalStrategy,
)


class TestProposalStrategy:
    """Test ProposalStrategy enum."""

    def test_proposal_strategy_values(self):
        """Test all proposal strategies are defined."""
        assert ProposalStrategy.GENETIC_ALGORITHM.value == "genetic_algorithm"
        assert ProposalStrategy.PARTICLE_SWARM.value == "particle_swarm"
        assert ProposalStrategy.DIFFERENTIAL_EVOLUTION.value == "differential_evolution"
        assert ProposalStrategy.CULTURAL_CONSENSUS.value == "cultural_consensus"

    def test_proposal_strategy_enum(self):
        """Test ProposalStrategy enum properties."""
        strategies = list(ProposalStrategy)
        assert len(strategies) == 4
        assert all(isinstance(s, ProposalStrategy) for s in strategies)


class TestProposal:
    """Test Proposal dataclass."""

    def test_proposal_creation(self):
        """Test creating a proposal."""
        proposal = Proposal(
            strategy="genetic_algorithm",
            improvements={"speed": 0.15, "accuracy": 0.08},
            fitness_estimate=0.85,
            confidence=0.9,
        )

        assert proposal.proposal_id is not None
        assert proposal.strategy == "genetic_algorithm"
        assert proposal.improvements["speed"] == 0.15
        assert proposal.fitness_estimate == 0.85
        assert proposal.confidence == 0.9

    def test_proposal_default_values(self):
        """Test proposal default values."""
        proposal = Proposal()

        assert proposal.proposal_id is not None
        assert proposal.strategy == "genetic_algorithm"
        assert proposal.improvements == {}
        assert proposal.fitness_estimate == 0.0
        assert proposal.confidence == 0.0
        assert proposal.novelty == 0.0
        assert proposal.generation == 0

    def test_proposal_to_dict(self):
        """Test proposal conversion to dictionary."""
        proposal = Proposal(
            strategy="particle_swarm",
            improvements={"param1": 0.5},
            fitness_estimate=0.8,
            confidence=0.85,
            novelty=0.6,
            generation=5,
            tags=["optimization", "convergence"],
        )

        proposal_dict = proposal.to_dict()

        assert "proposal_id" in proposal_dict
        assert proposal_dict["strategy"] == "particle_swarm"
        assert proposal_dict["fitness_estimate"] == 0.8
        assert proposal_dict["confidence"] == 0.85
        assert proposal_dict["novelty"] == 0.6
        assert proposal_dict["generation"] == 5
        assert "tags" in proposal_dict

    def test_proposal_with_parent_proposals(self):
        """Test proposal with parent tracking."""
        parent1 = Proposal()
        parent2 = Proposal()

        child = Proposal(
            parent_proposals=[parent1.proposal_id, parent2.proposal_id]
        )

        assert len(child.parent_proposals) == 2
        assert parent1.proposal_id in child.parent_proposals


class TestPopulationSnapshot:
    """Test PopulationSnapshot dataclass."""

    def test_snapshot_creation(self):
        """Test creating a population snapshot."""
        agents = [{"id": f"agent_{i}", "fitness": 0.5 + i * 0.1} for i in range(5)]
        fitness_scores = {f"agent_{i}": 0.5 + i * 0.1 for i in range(5)}

        snapshot = PopulationSnapshot(
            agents=agents,
            fitness_scores=fitness_scores,
            diversity_metric=0.7,
            avg_fitness=0.7,
            best_fitness=0.9,
            worst_fitness=0.5,
            generation=10,
        )

        assert len(snapshot.agents) == 5
        assert len(snapshot.fitness_scores) == 5
        assert snapshot.diversity_metric == 0.7
        assert snapshot.generation == 10

    def test_snapshot_metrics(self):
        """Test snapshot metric calculations."""
        fitness_scores = {
            "agent_0": 0.5,
            "agent_1": 0.7,
            "agent_2": 0.9,
            "agent_3": 0.6,
            "agent_4": 0.8,
        }

        snapshot = PopulationSnapshot(
            fitness_scores=fitness_scores,
            best_fitness=max(fitness_scores.values()),
            worst_fitness=min(fitness_scores.values()),
            avg_fitness=sum(fitness_scores.values()) / len(fitness_scores),
        )

        assert snapshot.best_fitness == 0.9
        assert snapshot.worst_fitness == 0.5
        assert snapshot.avg_fitness == 0.7


class TestMAEProposer:
    """Test MAEProposer main class."""

    def test_proposer_initialization(self):
        """Test MAEProposer initialization."""
        proposer = MAEProposer(
            population_size=20,
            proposal_batch_size=5,
            mutation_rate=0.1,
            crossover_rate=0.7,
        )

        assert proposer.population_size == 20
        assert proposer.proposal_batch_size == 5
        assert proposer.mutation_rate == 0.1
        assert proposer.crossover_rate == 0.7
        assert len(proposer.proposal_history) == 0

    @pytest.mark.asyncio
    async def test_proposer_genetic_algorithm_proposal(self):
        """Test genetic algorithm proposal generation."""
        proposer = MAEProposer(population_size=20)

        snapshot = PopulationSnapshot(
            agents=[{"id": f"agent_{i}", "genome": {"param": i * 0.1}} for i in range(10)],
            fitness_scores={f"agent_{i}": 0.5 + i * 0.05 for i in range(10)},
            avg_fitness=0.725,
            best_fitness=0.95,
            diversity_metric=0.6,
        )

        proposals = await proposer.propose_genetic_algorithm(snapshot)

        assert proposals is not None
        assert len(proposals) > 0
        assert all(p.strategy == ProposalStrategy.GENETIC_ALGORITHM.value for p in proposals)

    @pytest.mark.asyncio
    async def test_proposer_particle_swarm_proposal(self):
        """Test particle swarm optimization proposal."""
        proposer = MAEProposer(population_size=20)

        snapshot = PopulationSnapshot(
            agents=[{"id": f"agent_{i}", "position": [i * 0.1, i * 0.05]} for i in range(10)],
            fitness_scores={f"agent_{i}": 0.5 + i * 0.05 for i in range(10)},
            avg_fitness=0.725,
            best_fitness=0.95,
        )

        proposals = await proposer.propose_particle_swarm(snapshot)

        assert proposals is not None
        assert len(proposals) > 0

    def test_proposer_proposal_history(self):
        """Test proposal history tracking."""
        proposer = MAEProposer(population_size=10)

        proposal = Proposal(strategy="test", generation=1)
        proposer.proposal_history.append(proposal)

        assert len(proposer.proposal_history) == 1

    def test_proposer_generation_count(self):
        """Test generation count tracking."""
        proposer = MAEProposer(population_size=20)

        assert proposer.generation_count == 0
        proposer.generation_count += 1
        assert proposer.generation_count == 1

    def test_proposer_active_proposals(self):
        """Test active proposals tracking."""
        proposer = MAEProposer(population_size=20)

        proposal = Proposal(strategy="test")
        proposer.active_proposals[proposal.proposal_id] = proposal

        assert proposal.proposal_id in proposer.active_proposals
        assert len(proposer.active_proposals) == 1

    @pytest.mark.asyncio
    async def test_proposer_differential_evolution(self):
        """Test differential evolution proposal generation."""
        proposer = MAEProposer(population_size=20)

        snapshot = PopulationSnapshot(
            agents=[{"id": f"agent_{i}"} for i in range(10)],
            fitness_scores={f"agent_{i}": 0.5 + i * 0.05 for i in range(10)},
            avg_fitness=0.725,
        )

        proposals = await proposer.propose_differential_evolution(snapshot)

        assert proposals is not None
        assert len(proposals) > 0

    @pytest.mark.asyncio
    async def test_proposer_cultural_consensus(self):
        """Test cultural consensus proposal generation."""
        proposer = MAEProposer(population_size=20)

        snapshot = PopulationSnapshot(
            agents=[{"id": f"agent_{i}"} for i in range(10)],
            fitness_scores={f"agent_{i}": 0.5 + i * 0.05 for i in range(10)},
        )

        proposals = await proposer.propose_cultural_consensus(snapshot)

        assert proposals is not None

    def test_proposer_mutation_rate(self):
        """Test mutation rate configuration."""
        proposer = MAEProposer(mutation_rate=0.2)
        assert proposer.mutation_rate == 0.2

    def test_proposer_crossover_rate(self):
        """Test crossover rate configuration."""
        proposer = MAEProposer(crossover_rate=0.8)
        assert proposer.crossover_rate == 0.8


class TestProposalIntegration:
    """Integration tests for proposal system."""

    @pytest.mark.asyncio
    async def test_complete_proposal_cycle(self):
        """Test complete proposal generation and ranking cycle."""
        proposer = MAEProposer(
            population_size=30,
            proposal_batch_size=10,
        )

        # Create population snapshot
        snapshot = PopulationSnapshot(
            agents=[{"id": f"agent_{i}", "fitness": 0.5 + i * 0.02} for i in range(30)],
            fitness_scores={f"agent_{i}": 0.5 + i * 0.02 for i in range(30)},
            avg_fitness=0.79,
            best_fitness=0.99,
            worst_fitness=0.5,
            diversity_metric=0.65,
            generation=10,
        )

        # Generate proposals with genetic algorithm
        proposals = await proposer.propose_genetic_algorithm(snapshot)
        assert len(proposals) > 0

    @pytest.mark.asyncio
    async def test_multi_strategy_proposal_generation(self):
        """Test proposal generation with multiple strategies."""
        proposer = MAEProposer(population_size=20)

        snapshot = PopulationSnapshot(
            agents=[{"id": f"agent_{i}"} for i in range(20)],
            fitness_scores={f"agent_{i}": 0.5 for i in range(20)},
        )

        # Test multiple proposal strategies
        strategies = [
            (proposer.propose_genetic_algorithm, "genetic_algorithm"),
            (proposer.propose_particle_swarm, "particle_swarm"),
            (proposer.propose_differential_evolution, "differential_evolution"),
            (proposer.propose_cultural_consensus, "cultural_consensus"),
        ]

        for strategy_func, strategy_name in strategies:
            proposals = await strategy_func(snapshot)
            if proposals:
                assert all(isinstance(p, Proposal) for p in proposals)
