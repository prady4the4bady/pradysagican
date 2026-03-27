"""
LAYER 5: Multi-Agent Orchestration
==================================

8 autonomous agents with specialized roles that coordinate on complex tasks.

Agents:
1. ANALYZER - Deep investigation & problem decomposition
2. CODER - Software engineering & implementation
3. RESEARCHER - Knowledge discovery & research
4. PLANNER - Strategy & execution planning
5. CRITIC - Quality assurance & verification
6. LEARNER - Self-improvement & learning
7. MODERATOR - Team coordination & synthesis
8. GUARDIAN - Safety, ethics, compliance checks

Attribution: Patterns from CrewAI, AutoGen, and Multi-Agent Systems
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from enum import Enum

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════════
# AGENT ROLES
# ════════════════════════════════════════════════════════════════════════════

class AgentRole(str, Enum):
    """8 Agent roles"""
    ANALYZER = "analyzer"
    CODER = "coder"
    RESEARCHER = "researcher"
    PLANNER = "planner"
    CRITIC = "critic"
    LEARNER = "learner"
    MODERATOR = "moderator"
    GUARDIAN = "guardian"


@dataclass
class AgentConfig:
    """Configuration for an agent"""
    role: AgentRole
    name: str
    description: str
    system_prompt: str
    capabilities: List[str]
    preferred_tools: List[str]


# ════════════════════════════════════════════════════════════════════════════
# AGENT BASE CLASS
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class TaskResult:
    """Result from agent task execution"""
    agent_role: AgentRole
    task: str
    result: str
    confidence: float
    reasoning: str
    tools_used: List[str]
    duration_ms: float


class Agent:
    """Single autonomous agent"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.role = config.role
        self.name = config.name
        self.task_history: List[Dict[str, Any]] = []
        self.performance_score = 0.5
    
    async def execute_task(self, task: str, context: Dict[str, Any]) -> TaskResult:
        """Execute a task"""
        logger.info(f"[{self.name}] Executing task: {task[:50]}...")
        
        # Simulate task execution with role-specific behavior
        result_text, confidence, reasoning = await self._role_specific_execution(task, context)
        
        result = TaskResult(
            agent_role=self.role,
            task=task,
            result=result_text,
            confidence=confidence,
            reasoning=reasoning,
            tools_used=self.config.preferred_tools[:2],  # Use first 2 tools
            duration_ms=100.0
        )
        
        self.task_history.append({
            'task': task,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
        return result
    
    async def _role_specific_execution(self, task: str, context: Dict) -> tuple:
        """Role-specific task execution"""
        
        role_behaviors = {
            AgentRole.ANALYZER: self._analyzer_execution,
            AgentRole.CODER: self._coder_execution,
            AgentRole.RESEARCHER: self._researcher_execution,
            AgentRole.PLANNER: self._planner_execution,
            AgentRole.CRITIC: self._critic_execution,
            AgentRole.LEARNER: self._learner_execution,
            AgentRole.MODERATOR: self._moderator_execution,
            AgentRole.GUARDIAN: self._guardian_execution,
        }
        
        executor = role_behaviors.get(self.role)
        if executor:
            return await executor(task, context)
        
        return task, 0.5, "No role-specific executor"
    
    async def _analyzer_execution(self, task: str, context: Dict) -> tuple:
        """ANALYZER: Deep investigation"""
        result = f"Analysis of '{task}':\n"
        result += "- Key components identified\n"
        result += "- Dependencies mapped\n"
        result += "- Risks assessed\n"
        return result, 0.85, "Deep analysis complete"
    
    async def _coder_execution(self, task: str, context: Dict) -> tuple:
        """CODER: Implementation"""
        result = f"Implementation plan for: {task}\n"
        result += "```python\n"
        result += "# TODO: Implement functionality\n"
        result += "def solution():\n    pass\n```\n"
        return result, 0.8, "Code structure prepared"
    
    async def _researcher_execution(self, task: str, context: Dict) -> tuple:
        """RESEARCHER: Knowledge discovery"""
        result = f"Research findings on '{task}':\n"
        result += "- Source 1: Key insights\n"
        result += "- Source 2: Supporting evidence\n"
        result += "- Synthesis: Integrated findings\n"
        return result, 0.9, "Research synthesis complete"
    
    async def _planner_execution(self, task: str, context: Dict) -> tuple:
        """PLANNER: Strategy"""
        result = f"Strategic plan for: {task}\n"
        result += "Phase 1: Initial setup (2 hours)\n"
        result += "Phase 2: Core implementation (5 hours)\n"
        result += "Phase 3: Testing & refinement (3 hours)\n"
        return result, 0.8, "Plan timeline established"
    
    async def _critic_execution(self, task: str, context: Dict) -> tuple:
        """CRITIC: Quality verification"""
        result = f"Quality review of: {task}\n"
        result += "✓ Requirements met\n"
        result += "✓ No critical issues\n"
        result += "⚠ Minor improvements possible\n"
        return result, 0.82, "QA verification passed"
    
    async def _learner_execution(self, task: str, context: Dict) -> tuple:
        """LEARNER: Self-improvement"""
        result = f"Learning insights from: {task}\n"
        result += "- Technique 1 learned\n"
        result += "- Approach 2 optimized\n"
        result += "- Performance +15%\n"
        return result, 0.75, "Skill improvement recorded"
    
    async def _moderator_execution(self, task: str, context: Dict) -> tuple:
        """MODERATOR: Coordination"""
        result = f"Team coordination summary:\n"
        result += "- 5 agents engaged\n"
        result += "- 3 subtasks completed\n"
        result += "- Results synthesis in progress\n"
        return result, 0.88, "Team synchronization achieved"
    
    async def _guardian_execution(self, task: str, context: Dict) -> tuple:
        """GUARDIAN: Safety checks"""
        result = f"Safety assessment for: {task}\n"
        result += "✓ No security risks detected\n"
        result += "✓ Ethical compliance verified\n"
        result += "✓ Ready for deployment\n"
        return result, 0.95, "All safety gates passed"


# ════════════════════════════════════════════════════════════════════════════
# AGENT TEAM ORCHESTRATOR
# ════════════════════════════════════════════════════════════════════════════

class AgentTeam:
    """Orchestrates team of agents"""
    
    def __init__(self):
        self.agents: Dict[AgentRole, Agent] = {}
        self._initialize_agents()
        self.task_counter = 0
    
    def _initialize_agents(self):
        """Create all 8 agents"""
        configs = [
            AgentConfig(
                role=AgentRole.ANALYZER,
                name="Analyzer",
                description="Deep investigation and problem decomposition",
                system_prompt="You are an expert analyst. Break down complex problems into components.",
                capabilities=["analysis", "decomposition", "dependency_mapping"],
                preferred_tools=["analyze_code", "analyze_stats"]
            ),
            AgentConfig(
                role=AgentRole.CODER,
                name="Coder",
                description="Software engineering and implementation",
                system_prompt="You are a senior software engineer. Write clean, efficient code.",
                capabilities=["coding", "architecture", "refactoring"],
                preferred_tools=["generate_code", "execute_python"]
            ),
            AgentConfig(
                role=AgentRole.RESEARCHER,
                name="Researcher",
                description="Knowledge discovery and research",
                system_prompt="You are a research scientist. Discover new insights and patterns.",
                capabilities=["research", "discovery", "synthesis"],
                preferred_tools=["fetch_url", "analyze_stats"]
            ),
            AgentConfig(
                role=AgentRole.PLANNER,
                name="Planner",
                description="Strategy and execution planning",
                system_prompt="You are a strategic planner. Create detailed execution plans.",
                capabilities=["planning", "strategy", "timeline"],
                preferred_tools=["create_timeline", "plan_strategy"]
            ),
            AgentConfig(
                role=AgentRole.CRITIC,
                name="Critic",
                description="Quality assurance and verification",
                system_prompt="You are a QA expert. Verify quality and identify issues.",
                capabilities=["testing", "verification", "debugging"],
                preferred_tools=["execute_tests", "debug_code"]
            ),
            AgentConfig(
                role=AgentRole.LEARNER,
                name="Learner",
                description="Self-improvement and learning",
                system_prompt="You are always learning. Extract insights and improve capabilities.",
                capabilities=["learning", "optimization", "improvement"],
                preferred_tools=["analyze_performance", "extract_insights"]
            ),
            AgentConfig(
                role=AgentRole.MODERATOR,
                name="Moderator",
                description="Team coordination and synthesis",
                system_prompt="You coordinate the team. Synthesize results and manage flow.",
                capabilities=["coordination", "synthesis", "management"],
                preferred_tools=["summarize", "synthesize_results"]
            ),
            AgentConfig(
                role=AgentRole.GUARDIAN,
                name="Guardian",
                description="Safety, ethics, and compliance",
                system_prompt="You ensure safety and ethics. Check all constraints.",
                capabilities=["safety", "ethics", "compliance"],
                preferred_tools=["check_safety", "verify_compliance"]
            ),
        ]
        
        for config in configs:
            self.agents[config.role] = Agent(config)
    
    async def orchestrate_task(self, task: str, agent_roles: List[AgentRole] = None,
                              context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Orchestrate task execution across agent team
        """
        self.task_counter += 1
        task_id = f"task_{self.task_counter}"
        
        # Default: use all agents
        if agent_roles is None:
            agent_roles = list(AgentRole)
        
        context = context or {}
        print(f"\n[Team] Orchestrating task {task_id}")
        print(f"[Team] Task: {task}")
        print(f"[Team] Agents: {[r.value for r in agent_roles]}")
        
        # Execute in parallel
        tasks = []
        for role in agent_roles:
            if role in self.agents:
                tasks.append(self.agents[role].execute_task(task, context))
        
        results = await asyncio.gather(*tasks)
        
        # Synthesis & coordination
        synthesis = await self._synthesize_results(task_id, results, context)
        
        return {
            'task_id': task_id,
            'task': task,
            'agents_engaged': len(results),
            'individual_results': [
                {
                    'agent': r.agent_role.value,
                    'confidence': r.confidence,
                    'result': r.result[:100] + "..." if len(r.result) > 100 else r.result
                }
                for r in results
            ],
            'synthesis': synthesis,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _synthesize_results(self, task_id: str, results: List[TaskResult], 
                                 context: Dict) -> str:
        """Synthesize results from multiple agents"""
        moderator = self.agents[AgentRole.MODERATOR]
        
        synthesis_prompt = f"""
        Task: {task_id}
        
        Results from {len(results)} agents:
        """
        
        for result in results:
            synthesis_prompt += f"\n- {result.agent_role.value}: {result.result[:50]}..."
        
        # Moderator synthesizes
        synthesis_result = await moderator.execute_task(synthesis_prompt, context)
        
        return synthesis_result.result
    
    async def get_team_status(self) -> Dict[str, Any]:
        """Get team performance status"""
        return {
            'total_agents': len(self.agents),
            'agents': {
                role.value: {
                    'name': agent.name,
                    'role': role.value,
                    'tasks_completed': len(agent.task_history),
                    'performance': agent.performance_score,
                }
                for role, agent in self.agents.items()
            },
            'tasks_total': self.task_counter
        }


# ════════════════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════════════════

async def demo_agent_team():
    """Demonstrate multi-agent orchestration"""
    print("\n" + "="*70)
    print("LAYER 5: MULTI-AGENT ORCHESTRATION DEMO")
    print("="*70)
    
    team = AgentTeam()
    
    # Task 1: Simple request
    print("\n[Demo] Task 1: Analysis Request")
    result1 = await team.orchestrate_task(
        task="Analyze the performance of a REST API",
        agent_roles=[AgentRole.ANALYZER, AgentRole.CRITIC, AgentRole.MODERATOR]
    )
    print(f"Result: {result1['synthesis'][:200]}...")
    
    # Task 2: Complex request
    print("\n[Demo] Task 2: Full System Design")
    result2 = await team.orchestrate_task(
        task="Design a microservices architecture for an e-commerce platform",
        agent_roles=list(AgentRole)  # All agents
    )
    print(f"Agents engaged: {result2['agents_engaged']}")
    
    # Task 3: Code implementation
    print("\n[Demo] Task 3: Code Implementation")
    result3 = await team.orchestrate_task(
        task="Implement a priority queue data structure",
        agent_roles=[AgentRole.CODER, AgentRole.CRITIC, AgentRole.LEARNER]
    )
    print(f"Result: {result3['synthesis'][:200]}...")
    
    # Team status
    print("\n[Team] Final Status:")
    status = await team.get_team_status()
    print(f"  Total agents: {status['total_agents']}")
    print(f"  Total tasks: {status['tasks_total']}")
    for role_name, agent_info in status['agents'].items():
        print(f"    {role_name:12}: {agent_info['tasks_completed']} tasks completed")


if __name__ == "__main__":
    asyncio.run(demo_agent_team())
