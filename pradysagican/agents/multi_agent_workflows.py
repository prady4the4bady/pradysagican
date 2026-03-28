"""
PHASE 14: AGENT FRAMEWORK TIER 3
================================
Multi-agent workflows and orchestration patterns.

Workflow types:
- Sequential: Agents execute one after another
- Concurrent: Agents execute in parallel
- Hierarchical: Boss-worker pattern with delegation
- Human-in-Loop: Human-agent collaboration
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from enum import Enum

from pradysagican.agents.specialized_agents import (
    ResearcherAgent,
    AnalystAgent,
    EngineerAgent,
    CreatorAgent,
    OracleAgent
)

logger = logging.getLogger(__name__)


class WorkflowType(str, Enum):
    """Types of multi-agent workflows."""
    SEQUENTIAL = "sequential"
    CONCURRENT = "concurrent"
    HIERARCHICAL = "hierarchical"
    HUMAN_IN_LOOP = "human_in_loop"


@dataclass
class WorkflowStep:
    """Single step in a workflow."""
    step_id: str
    agent_type: str  # "researcher", "analyst", "engineer", "creator", "oracle"
    task: str
    input_data: Dict[str, Any]
    status: str = "pending"  # pending, running, completed, failed
    output_data: Optional[Dict[str, Any]] = None
    execution_time_ms: float = 0.0


@dataclass
class WorkflowResult:
    """Result of workflow execution."""
    workflow_id: str
    workflow_type: WorkflowType
    steps_completed: int
    total_steps: int
    success: bool
    execution_time_ms: float
    outputs: List[Dict[str, Any]] = field(default_factory=list)


class SequentialWorkflow:
    """Execute agents sequentially - output of one feeds into next."""
    
    def __init__(self, name: str = "SequentialWorkflow"):
        self.name = name
        self.steps: List[WorkflowStep] = []
        self.agents = {
            "researcher": ResearcherAgent(),
            "analyst": AnalystAgent(),
            "engineer": EngineerAgent(),
            "creator": CreatorAgent(),
            "oracle": OracleAgent()
        }
    
    def add_step(self, step_id: str, agent_type: str, task: str, input_data: Dict[str, Any]):
        """Add a step to the workflow."""
        step = WorkflowStep(step_id, agent_type, task, input_data)
        self.steps.append(step)
    
    async def execute(self) -> WorkflowResult:
        """Execute workflow sequentially."""
        start_time = datetime.now()
        outputs = []
        completed = 0
        
        for step in self.steps:
            step.status = "running"
            
            try:
                agent = self.agents.get(step.agent_type)
                if not agent:
                    step.status = "failed"
                    continue
                
                # Execute based on agent type
                if step.agent_type == "researcher":
                    result = await agent.conduct_research(step.task)
                elif step.agent_type == "analyst":
                    result = await agent.analyze_data(step.input_data)
                elif step.agent_type == "engineer":
                    result = await agent.design_architecture(step.input_data)
                elif step.agent_type == "creator":
                    result = await agent.generate_ideas(step.task)
                elif step.agent_type == "oracle":
                    result = await agent.predict_future(step.input_data)
                else:
                    result = {}
                
                step.output_data = result
                step.status = "completed"
                completed += 1
                outputs.append(result)
                
            except Exception as e:
                step.status = "failed"
                step.output_data = {"error": str(e)}
        
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return WorkflowResult(
            workflow_id=f"sequential_{len(self.steps)}",
            workflow_type=WorkflowType.SEQUENTIAL,
            steps_completed=completed,
            total_steps=len(self.steps),
            success=completed == len(self.steps),
            execution_time_ms=execution_time_ms,
            outputs=outputs
        )


class ConcurrentWorkflow:
    """Execute agents concurrently - parallel execution."""
    
    def __init__(self, name: str = "ConcurrentWorkflow"):
        self.name = name
        self.steps: List[WorkflowStep] = []
        self.agents = {
            "researcher": ResearcherAgent(),
            "analyst": AnalystAgent(),
            "engineer": EngineerAgent(),
            "creator": CreatorAgent(),
            "oracle": OracleAgent()
        }
    
    def add_step(self, step_id: str, agent_type: str, task: str, input_data: Dict[str, Any]):
        """Add a step to the workflow."""
        step = WorkflowStep(step_id, agent_type, task, input_data)
        self.steps.append(step)
    
    async def _execute_step(self, step: WorkflowStep) -> Dict[str, Any]:
        """Execute a single step."""
        try:
            agent = self.agents.get(step.agent_type)
            if not agent:
                return {"error": f"Agent type {step.agent_type} not found"}
            
            if step.agent_type == "researcher":
                return await agent.conduct_research(step.task)
            elif step.agent_type == "analyst":
                return await agent.analyze_data(step.input_data)
            elif step.agent_type == "engineer":
                return await agent.design_architecture(step.input_data)
            elif step.agent_type == "creator":
                return await agent.generate_ideas(step.task)
            elif step.agent_type == "oracle":
                return await agent.predict_future(step.input_data)
            else:
                return {}
        except Exception as e:
            return {"error": str(e)}
    
    async def execute(self) -> WorkflowResult:
        """Execute workflow concurrently."""
        start_time = datetime.now()
        
        # Run all steps concurrently
        tasks = [self._execute_step(step) for step in self.steps]
        results = await asyncio.gather(*tasks)
        
        # Update step status
        for step, result in zip(self.steps, results):
            step.output_data = result
            step.status = "completed" if "error" not in result else "failed"
        
        completed = sum(1 for s in self.steps if s.status == "completed")
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return WorkflowResult(
            workflow_id=f"concurrent_{len(self.steps)}",
            workflow_type=WorkflowType.CONCURRENT,
            steps_completed=completed,
            total_steps=len(self.steps),
            success=completed == len(self.steps),
            execution_time_ms=execution_time_ms,
            outputs=results
        )


class HierarchicalWorkflow:
    """Boss-worker pattern where boss coordinates workers."""
    
    def __init__(self, name: str = "HierarchicalWorkflow"):
        self.name = name
        self.boss_agent = OracleAgent()  # Boss makes strategic decisions
        self.worker_agents = {
            "researcher": ResearcherAgent(),
            "analyst": AnalystAgent(),
            "engineer": EngineerAgent(),
            "creator": CreatorAgent()
        }
        self.delegations: List[Dict[str, Any]] = []
    
    async def coordinate_work(self, objective: str) -> WorkflowResult:
        """Boss coordinates work toward objective."""
        start_time = datetime.now()
        outputs = []
        completed = 0
        
        # Boss creates strategic plan
        strategic_plan = await self.boss_agent.provide_strategic_guidance({
            "objective": objective
        })
        
        # Boss delegates to workers based on plan
        delegations = [
            {"agent": "researcher", "task": f"Research aspects of {objective}"},
            {"agent": "analyst", "task": f"Analyze {objective} data"},
            {"agent": "creator", "task": f"Create solutions for {objective}"},
            {"agent": "engineer", "task": f"Design implementation of {objective}"}
        ]
        
        # Workers execute delegated tasks
        for delegation in delegations:
            agent_type = delegation["agent"]
            agent = self.worker_agents.get(agent_type)
            
            if agent_type == "researcher":
                result = await agent.conduct_research(delegation["task"])
            elif agent_type == "analyst":
                result = await agent.analyze_data({})
            elif agent_type == "creator":
                result = await agent.generate_ideas(delegation["task"])
            elif agent_type == "engineer":
                result = await agent.design_architecture({})
            else:
                result = {}
            
            outputs.append(result)
            completed += 1
            self.delegations.append(delegation)
        
        # Boss synthesizes results
        synthesis = await self.boss_agent.predict_future({
            "worker_outputs": outputs
        })
        outputs.append(synthesis)
        
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return WorkflowResult(
            workflow_id=f"hierarchical_{len(self.delegations)}",
            workflow_type=WorkflowType.HIERARCHICAL,
            steps_completed=completed + 1,
            total_steps=len(delegations) + 1,
            success=True,
            execution_time_ms=execution_time_ms,
            outputs=outputs
        )


class HumanInLoopWorkflow:
    """Workflow with human feedback and approval steps."""
    
    def __init__(self, name: str = "HumanInLoopWorkflow"):
        self.name = name
        self.analyst = AnalystAgent()
        self.oracle = OracleAgent()
        self.approval_steps: List[Dict[str, Any]] = []
    
    async def run_with_approval(self, task_description: str, 
                               approval_callback: Optional[Callable] = None) -> WorkflowResult:
        """Run workflow with human approval steps."""
        start_time = datetime.now()
        outputs = []
        
        # Step 1: Analyst generates analysis
        analysis = await self.analyst.analyze_data({"task": task_description})
        outputs.append(analysis)
        
        # Step 2: Request human approval
        approval_status = "approved"  # In real scenario, would wait for human input
        if approval_callback:
            approval_status = await approval_callback(analysis)
        
        self.approval_steps.append({
            "step": "analysis_approval",
            "status": approval_status,
            "timestamp": datetime.now().isoformat()
        })
        
        # Step 3: Oracle provides guidance if approved
        if approval_status == "approved":
            guidance = await self.oracle.provide_strategic_guidance({
                "analysis": analysis
            })
            outputs.append(guidance)
        
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return WorkflowResult(
            workflow_id=f"human_in_loop",
            workflow_type=WorkflowType.HUMAN_IN_LOOP,
            steps_completed=len(outputs),
            total_steps=3,
            success=True,
            execution_time_ms=execution_time_ms,
            outputs=outputs
        )


async def demonstrate_all_workflows():
    """Demonstrate all workflow types."""
    
    results = {}
    
    # Sequential Workflow
    seq_workflow = SequentialWorkflow("Research→Analysis→Implementation")
    seq_workflow.add_step("s1", "researcher", "AI Safety", {})
    seq_workflow.add_step("s2", "analyst", "Analyze findings", {})
    seq_workflow.add_step("s3", "engineer", "Design solution", {})
    seq_result = await seq_workflow.execute()
    results["sequential"] = {
        "type": "Sequential",
        "steps": seq_result.steps_completed,
        "success": seq_result.success,
        "time_ms": seq_result.execution_time_ms
    }
    
    # Concurrent Workflow
    conc_workflow = ConcurrentWorkflow("Parallel Analysis")
    conc_workflow.add_step("c1", "researcher", "Research", {})
    conc_workflow.add_step("c2", "analyst", "Analyze", {})
    conc_workflow.add_step("c3", "creator", "Generate Ideas", {})
    conc_result = await conc_workflow.execute()
    results["concurrent"] = {
        "type": "Concurrent",
        "steps": conc_result.steps_completed,
        "success": conc_result.success,
        "time_ms": conc_result.execution_time_ms
    }
    
    # Hierarchical Workflow
    hier_workflow = HierarchicalWorkflow("Boss-Worker Coordination")
    hier_result = await hier_workflow.coordinate_work("Build AI System")
    results["hierarchical"] = {
        "type": "Hierarchical",
        "steps": hier_result.steps_completed,
        "success": hier_result.success,
        "time_ms": hier_result.execution_time_ms
    }
    
    # Human-in-Loop Workflow
    human_workflow = HumanInLoopWorkflow("Human-Approved Process")
    human_result = await human_workflow.run_with_approval("Review Decision")
    results["human_in_loop"] = {
        "type": "Human-in-Loop",
        "steps": human_result.steps_completed,
        "success": human_result.success,
        "time_ms": human_result.execution_time_ms
    }
    
    return {
        "workflows_executed": 4,
        "results": results,
        "all_successful": all(r["success"] for r in results.values())
    }
