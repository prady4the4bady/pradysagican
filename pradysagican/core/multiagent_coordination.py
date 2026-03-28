#!/usr/bin/env python3
"""
PHASE 10: MULTI-AGENT COORDINATION
Multiple PRADYSAGICAN instances coordinating together
"""

import asyncio
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class MessageType(Enum):
    """Types of inter-agent messages"""
    TASK = "task"              # Assign task
    RESULT = "result"          # Return result
    QUERY = "query"            # Ask for help
    SHARE_KNOWLEDGE = "share"  # Share discovery
    COORDINATE = "coordinate"  # Coordinate action
    VOTE = "vote"              # Distributed voting


@dataclass
class Message:
    """Inter-agent message"""
    sender_id: str
    receiver_id: str
    message_type: MessageType
    content: Dict
    priority: int = 0


class CommunicationBus:
    """Manages message passing between agents"""
    
    def __init__(self):
        self.message_queue: List[Message] = []
        self.message_history: List[Message] = []
    
    async def send(self, message: Message) -> None:
        """Send message on bus"""
        self.message_queue.append(message)
        self.message_history.append(message)
    
    async def receive(self, agent_id: str) -> List[Message]:
        """Get messages for agent"""
        messages = [m for m in self.message_queue if m.receiver_id == agent_id]
        
        # Remove from queue
        for m in messages:
            self.message_queue.remove(m)
        
        return sorted(messages, key=lambda m: m.priority, reverse=True)


class DistributedVotingSystem:
    """Quorum-based decision making"""
    
    def __init__(self, quorum_threshold: float = 0.66):
        self.quorum_threshold = quorum_threshold
        self.vote_history: List[Dict] = []
    
    async def call_vote(self, issue: str, agents: List[str], 
                       positions: Dict[str, bool]) -> Tuple[bool, float]:
        """Call vote on issue"""
        
        # Count votes
        for_count = sum(1 for v in positions.values() if v)
        against_count = len(positions) - for_count
        
        agreement = for_count / len(positions) if positions else 0
        
        # Check quorum
        passed = agreement >= self.quorum_threshold
        
        self.vote_history.append({
            'issue': issue,
            'for': for_count,
            'against': against_count,
            'agreement': agreement,
            'passed': passed
        })
        
        return passed, agreement
    
    async def get_consensus_decision(self, decisions: Dict[str, float]) -> float:
        """Get consensus from multiple agents"""
        
        if not decisions:
            return 0.5
        
        values = list(decisions.values())
        return sum(values) / len(values)


class CoordinationAgent:
    """Agent capable of multi-agent coordination"""
    
    def __init__(self, agent_id: str, bus: CommunicationBus):
        self.agent_id = agent_id
        self.bus = bus
        self.knowledge: Dict[str, float] = {}
        self.completed_tasks = 0
    
    async def receive_messages(self) -> List[Message]:
        """Receive messages from bus"""
        return await self.bus.receive(self.agent_id)
    
    async def send_message(self, receiver_id: str, message_type: MessageType,
                          content: Dict, priority: int = 0) -> None:
        """Send message to other agent"""
        message = Message(
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            message_type=message_type,
            content=content,
            priority=priority
        )
        await self.bus.send(message)
    
    async def share_knowledge(self, knowledge: Dict) -> None:
        """Share knowledge with all other agents"""
        self.knowledge.update(knowledge)
    
    async def execute_task(self) -> float:
        """Execute assigned task"""
        # Simulate task execution
        result = random.random()
        self.completed_tasks += 1
        return result


class MultiAgentCoordinator:
    """Orchestrates multiple agents"""
    
    def __init__(self, num_agents: int = 5):
        self.num_agents = num_agents
        self.bus = CommunicationBus()
        self.agents = [CoordinationAgent(f"agent_{i}", self.bus) 
                      for i in range(num_agents)]
        self.voting_system = DistributedVotingSystem()
        self.coordination_history: List[Dict] = []
    
    async def broadcast_task(self, task_id: str, content: Dict) -> None:
        """Broadcast task to all agents"""
        for agent in self.agents:
            await agent.send_message(agent.agent_id, MessageType.TASK,
                                    {'task_id': task_id, **content})
    
    async def execute_parallel_tasks(self, num_tasks: int = 3) -> Dict:
        """Execute tasks in parallel across agents"""
        
        results = {
            'tasks_assigned': num_tasks,
            'results': [],
            'total_completed': 0
        }
        
        # Assign tasks
        for task_idx in range(num_tasks):
            agent = self.agents[task_idx % len(self.agents)]
            result = await agent.execute_task()
            results['results'].append(result)
            results['total_completed'] += 1
        
        return results
    
    async def coordinate_decision(self, issue: str) -> Tuple[bool, float]:
        """Make decision through voting"""
        
        # Get positions from all agents
        positions = {}
        for agent in self.agents:
            # Each agent has opinion (simplified: random)
            position = random.random() > 0.5
            positions[agent.agent_id] = position
        
        # Call vote
        passed, agreement = await self.voting_system.call_vote(issue, 
                                                               [a.agent_id for a in self.agents],
                                                               positions)
        
        self.coordination_history.append({
            'issue': issue,
            'passed': passed,
            'agreement': agreement
        })
        
        return passed, agreement
    
    async def knowledge_sharing_round(self) -> Dict:
        """Round of knowledge sharing"""
        
        shared_knowledge = {}
        
        # Each agent shares knowledge with others
        for agent in self.agents:
            knowledge = {
                f'discovery_{agent.agent_id}': random.random()
            }
            shared_knowledge[agent.agent_id] = knowledge
            
            # Broadcast to others
            for other in self.agents:
                if other.agent_id != agent.agent_id:
                    await agent.send_message(other.agent_id, 
                                           MessageType.SHARE_KNOWLEDGE,
                                           knowledge)
        
        # All agents receive and integrate
        total_knowledge = 0
        for agent in self.agents:
            messages = await agent.receive_messages()
            for msg in messages:
                if msg.message_type == MessageType.SHARE_KNOWLEDGE:
                    agent.knowledge.update(msg.content)
                    total_knowledge += len(msg.content)
        
        return {
            'agents': len(self.agents),
            'knowledge_items_shared': total_knowledge,
            'avg_knowledge_per_agent': total_knowledge / len(self.agents) if self.agents else 0
        }
    
    async def run_coordination_cycle(self, cycles: int = 3) -> Dict:
        """Run complete coordination cycle"""
        
        stats = {
            'cycles': cycles,
            'total_tasks': 0,
            'voting_decisions': 0,
            'knowledge_shared': 0
        }
        
        for cycle in range(cycles):
            # Parallel task execution
            task_results = await self.execute_parallel_tasks(2)
            stats['total_tasks'] += task_results['total_completed']
            
            # Voting on decision
            passed, agreement = await self.coordinate_decision(f"decision_{cycle}")
            stats['voting_decisions'] += 1
            
            # Knowledge sharing
            sharing = await self.knowledge_sharing_round()
            stats['knowledge_shared'] += sharing['knowledge_items_shared']
        
        return stats


# ════════════════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════════════════

async def demo_multiagent_coordination():
    """Demonstrate multi-agent coordination"""
    
    print("\n" + "=" * 70)
    print("MULTI-AGENT COORDINATION (PHASE 10)")
    print("=" * 70)
    
    # Initialize coordinator
    print("\n[Setup] Initializing multi-agent system...")
    coordinator = MultiAgentCoordinator(num_agents=5)
    print(f"  Agents: {len(coordinator.agents)}")
    
    # Parallel task execution
    print("\n[Execution] Running parallel tasks...")
    task_results = await coordinator.execute_parallel_tasks(num_tasks=3)
    print(f"  Tasks completed: {task_results['total_completed']}")
    for i, result in enumerate(task_results['results']):
        print(f"    Task {i}: {result:.3f}")
    
    # Voting
    print("\n[Voting] Testing distributed decision making...")
    for i in range(2):
        passed, agreement = await coordinator.coordinate_decision(f"proposal_{i}")
        print(f"  Proposal {i}: {'PASSED' if passed else 'REJECTED'} (agreement: {agreement:.1%})")
    
    # Knowledge sharing
    print("\n[Knowledge] Running knowledge sharing round...")
    sharing = await coordinator.knowledge_sharing_round()
    print(f"  Knowledge items shared: {sharing['knowledge_items_shared']}")
    print(f"  Avg per agent: {sharing['avg_knowledge_per_agent']:.1f}")
    
    # Full coordination cycle
    print("\n[Coordination] Running 3-cycle coordination...")
    stats = await coordinator.run_coordination_cycle(cycles=3)
    
    print(f"  Total tasks: {stats['total_tasks']}")
    print(f"  Voting decisions: {stats['voting_decisions']}")
    print(f"  Knowledge items: {stats['knowledge_shared']}")
    
    # Statistics
    print("\n[Statistics]:")
    print(f"  Agents: {len(coordinator.agents)}")
    print(f"  Message bus history: {len(coordinator.bus.message_history)} messages")
    print(f"  Voting history: {len(coordinator.voting_system.vote_history)} votes")
    print(f"  Coordination history: {len(coordinator.coordination_history)} decisions")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(demo_multiagent_coordination())
