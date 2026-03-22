"""Agent modules: stark_core, orchestrator, strategist, ethics, learner, inventor."""
from pradysagican.agents.stark_core import StarkCore, StarkMindset, DecisionJournal, OperatorDashboard, RapidExperimenter
from pradysagican.agents.orchestrator import MasterOrchestrator, AgentRole, TaskPriority, SubAgent, TaskNode, SwarmProtocol, MessageBus
from pradysagican.agents.strategist import StrategicPlanner, Strategy, SWOTAnalysis, WarGame, SimulationResult
from pradysagican.agents.ethics import EthicsGuardian, EthicalAssessment, Stakeholder, Consequence, BiasReport
from pradysagican.agents.learner import SelfImprovementEngine, LearningEpisode, SkillTree, Heuristic, SelfModification
from pradysagican.agents.inventor import InventionEngine, Invention, Hypothesis, InnovationMatrix, ResearchPipeline, PatentAnalyser

__all__ = [
    # Stark Core
    "StarkCore", "StarkMindset", "DecisionJournal", "OperatorDashboard", "RapidExperimenter",
    # Orchestrator
    "MasterOrchestrator", "AgentRole", "TaskPriority", "SubAgent", "TaskNode", "SwarmProtocol", "MessageBus",
    # Strategist
    "StrategicPlanner", "Strategy", "SWOTAnalysis", "WarGame", "SimulationResult",
    # Ethics
    "EthicsGuardian", "EthicalAssessment", "Stakeholder", "Consequence", "BiasReport",
    # Learner
    "SelfImprovementEngine", "LearningEpisode", "SkillTree", "Heuristic", "SelfModification",
    # Inventor
    "InventionEngine", "Invention", "Hypothesis", "InnovationMatrix", "ResearchPipeline", "PatentAnalyser",
]
