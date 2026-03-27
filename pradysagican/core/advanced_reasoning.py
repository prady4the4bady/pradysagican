"""
ADVANCED: Debate & Multi-Perspective Reasoning
=======================

Generate pro/con arguments, devil's advocate,
Socratic questioning, and consensus reasoning.

Attribution: Debate algorithms, multi-agent reasoning,
dialectical reasoning patterns
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════════
# DEBATE COMPONENTS
# ════════════════════════════════════════════════════════════════════════════

class PerspectiveType(str, Enum):
    """Types of perspectives in debate"""
    PRO = "pro"
    CON = "con"
    NEUTRAL = "neutral"
    DEVIL_ADVOCATE = "devil_advocate"
    SOCRATIC = "socratic"


@dataclass
class Argument:
    """Single argument"""
    position: str  # Pro or Con
    thesis: str
    evidence: List[str]
    counter_arguments: List[str] = field(default_factory=list)
    strength: float = 0.5  # 0.0 to 1.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Perspective:
    """Complete perspective on a topic"""
    perspective_type: PerspectiveType
    title: str
    arguments: List[Argument]
    conclusion: str
    confidence: float = 0.5


class ArgumentGenerator:
    """Generate structured arguments"""
    
    async def generate_pro_arguments(self, topic: str, 
                                    depth: int = 3) -> List[Argument]:
        """Generate pro arguments"""
        arguments = []
        
        pro_templates = [
            f"This approach enables {topic}",
            f"Research demonstrates that {topic}",
            f"Practically, {topic}",
            f"From a policy perspective, {topic}",
            f"Evidence-based studies show {topic}",
        ]
        
        for i, template in enumerate(pro_templates[:depth]):
            arg = Argument(
                position="pro",
                thesis=template,
                evidence=[
                    f"Study {i+1}: Supporting evidence A",
                    f"Study {i+1}: Supporting evidence B",
                    f"Expert consensus: Point C",
                ],
                counter_arguments=[
                    "Critics argue limitation X",
                    "However, implementation may face Y",
                ],
                strength=0.7 + (i * 0.05)
            )
            arguments.append(arg)
        
        return arguments
    
    async def generate_con_arguments(self, topic: str, 
                                    depth: int = 3) -> List[Argument]:
        """Generate con arguments"""
        arguments = []
        
        con_templates = [
            f"The limitations of {topic}",
            f"Practical challenges in {topic}",
            f"Economic constraints on {topic}",
            f"Risk factors in {topic}",
            f"Alternative approaches better than {topic}",
        ]
        
        for i, template in enumerate(con_templates[:depth]):
            arg = Argument(
                position="con",
                thesis=template,
                evidence=[
                    f"Counter-evidence {i+1}: Risk A",
                    f"Counter-evidence {i+1}: Cost B",
                    f"Historical precedent: Lesson C",
                ],
                counter_arguments=[
                    "Proponents note advantage X",
                    "Technology may mitigate issue Y",
                ],
                strength=0.65 + (i * 0.03)
            )
            arguments.append(arg)
        
        return arguments


# ════════════════════════════════════════════════════════════════════════════
# DEBATE ORCHESTRATION
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class DebateRound:
    """Single debate round"""
    round_number: int
    pro_arguments: List[Argument]
    con_arguments: List[Argument]
    rebuttals_pro: List[str] = field(default_factory=list)
    rebuttals_con: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class DebateSession:
    """Structured debate session"""
    
    def __init__(self, topic: str, num_rounds: int = 3):
        self.topic = topic
        self.num_rounds = num_rounds
        self.rounds: List[DebateRound] = []
        self.arg_generator = ArgumentGenerator()
    
    async def conduct_debate(self) -> Dict[str, Any]:
        """Conduct full debate"""
        
        for round_num in range(1, self.num_rounds + 1):
            # Generate arguments
            pro_args = await self.arg_generator.generate_pro_arguments(
                self.topic, depth=2
            )
            con_args = await self.arg_generator.generate_con_arguments(
                self.topic, depth=2
            )
            
            # Generate rebuttals
            pro_rebuttals = [
                f"The con argument about limitation X overlooks benefit Y",
                f"Evidence contradicts the claim that Z",
            ]
            
            con_rebuttals = [
                f"While benefits are noted, risks outweigh them",
                f"The evidence presented is outdated and doesn't reflect current reality",
            ]
            
            # Create round
            round_data = DebateRound(
                round_number=round_num,
                pro_arguments=pro_args,
                con_arguments=con_args,
                rebuttals_pro=pro_rebuttals,
                rebuttals_con=con_rebuttals,
            )
            
            self.rounds.append(round_data)
        
        return await self.summarize_debate()
    
    async def summarize_debate(self) -> Dict[str, Any]:
        """Summarize debate results"""
        
        total_pro_strength = sum(
            sum(arg.strength for arg in round.pro_arguments)
            for round in self.rounds
        )
        
        total_con_strength = sum(
            sum(arg.strength for arg in round.con_arguments)
            for round in self.rounds
        )
        
        pro_wins = total_pro_strength > total_con_strength
        
        return {
            'topic': self.topic,
            'rounds': len(self.rounds),
            'pro_total_strength': total_pro_strength,
            'con_total_strength': total_con_strength,
            'stronger_position': 'pro' if pro_wins else 'con',
            'confidence': max(total_pro_strength, total_con_strength) / (total_pro_strength + total_con_strength),
            'rounds_detail': [
                {
                    'round': r.round_number,
                    'pro_count': len(r.pro_arguments),
                    'con_count': len(r.con_arguments),
                    'pro_strength': sum(a.strength for a in r.pro_arguments),
                    'con_strength': sum(a.strength for a in r.con_arguments),
                }
                for r in self.rounds
            ]
        }


# ════════════════════════════════════════════════════════════════════════════
# SOCRATIC QUESTIONING
# ════════════════════════════════════════════════════════════════════════════

class SocraticQuestioner:
    """Generate Socratic questions to deepen reasoning"""
    
    def __init__(self):
        self.question_types = [
            "clarification",
            "assumption",
            "reasoning",
            "implication",
            "perspective",
            "evidence",
        ]
    
    async def generate_questions(self, claim: str, 
                                depth: int = 5) -> List[str]:
        """Generate Socratic questions"""
        
        questions = [
            f"What exactly do you mean by '{claim.split()[0]}'?",
            f"How do you know that {claim}?",
            f"What evidence supports this claim?",
            f"Could there be a counter-example to {claim}?",
            f"What would someone opposed to this view say?",
        ]
        
        return questions[:depth]
    
    async def challenge_assumption(self, assumption: str) -> List[str]:
        """Challenge an assumption"""
        
        challenges = [
            f"Is the assumption that '{assumption}' actually justified?",
            f"What if {assumption} were false? What would change?",
            f"Are there hidden assumptions within '{assumption}'?",
            f"How would we test whether '{assumption}' is true?",
            f"What evidence would disprove '{assumption}'?",
        ]
        
        return challenges
    
    async def explore_implications(self, statement: str) -> List[str]:
        """Explore implications of a statement"""
        
        implications = [
            f"If {statement}, then what follows?",
            f"What would be the long-term implications of '{statement}'?",
            f"Who would be affected by the claim that {statement}?",
            f"How does '{statement}' connect to related ideas?",
            f"Could '{statement}' lead to unintended consequences?",
        ]
        
        return implications


# ════════════════════════════════════════════════════════════════════════════
# DEVIL'S ADVOCATE
# ════════════════════════════════════════════════════════════════════════════

class DevilsAdvocate:
    """Generate opposing view for any position"""
    
    async def generate_opposition(self, position: str,
                                 strength: str = "strong") -> Dict[str, Any]:
        """Generate opposing viewpoint"""
        
        opposition_templates = {
            'strong': [
                f"Contrary to {position}, we should consider...",
                f"While {position} has merit, fundamentally...",
                f"The evidence actually suggests the opposite of {position}",
            ],
            'moderate': [
                f"A reasonable objection to {position} is...",
                f"One limitation of {position} might be...",
                f"Some would argue that {position} overlooks...",
            ],
            'weak': [
                f"A minor point against {position} could be...",
                f"In some contexts, {position} might not apply...",
                f"One could quibble with {position} by noting...",
            ]
        }
        
        templates = opposition_templates.get(strength, opposition_templates['moderate'])
        
        return {
            'original_position': position,
            'opposition_statement': templates[0],
            'key_objections': [
                'Practicality concern',
                'Evidence limitation',
                'Alternative interpretation',
            ],
            'counter_counter_arguments': [
                'However, the original position withstands this objection because...',
                'This criticism presumes that X, which is questionable',
            ],
            'confidence': 0.6 if strength == 'weak' else (0.75 if strength == 'moderate' else 0.85),
        }


# ════════════════════════════════════════════════════════════════════════════
# MULTI-PERSPECTIVE REASONING
# ════════════════════════════════════════════════════════════════════════════

class MultiPerspectiveAnalyzer:
    """Analyze question from multiple perspectives"""
    
    def __init__(self):
        self.questioner = SocraticQuestioner()
        self.advocate = DevilsAdvocate()
    
    async def analyze_from_perspectives(self, question: str,
                                       perspectives: List[str] = None) -> Dict[str, Any]:
        """Analyze from multiple perspectives"""
        
        if perspectives is None:
            perspectives = [
                'scientific',
                'philosophical',
                'practical',
                'ethical',
                'economic',
            ]
        
        analysis = {
            'question': question,
            'perspectives': {},
        }
        
        for perspective in perspectives:
            analysis['perspectives'][perspective] = {
                'angle': f"From a {perspective} perspective, {question}",
                'key_questions': await self.questioner.generate_questions(question, depth=2),
                'concerns': [
                    f"{perspective} concern A",
                    f"{perspective} concern B",
                ],
                'insights': [
                    f"{perspective} insight X",
                    f"{perspective} insight Y",
                ],
            }
        
        return analysis
    
    async def find_consensus(self, perspectives: Dict[str, Any]) -> Dict[str, Any]:
        """Find consensus among perspectives"""
        
        # Identify common themes
        all_concerns = []
        all_insights = []
        
        for perspective_data in perspectives.values():
            all_concerns.extend(perspective_data.get('concerns', []))
            all_insights.extend(perspective_data.get('insights', []))
        
        return {
            'common_themes': list(set(all_insights))[:3],
            'shared_concerns': list(set(all_concerns))[:3],
            'points_of_agreement': [
                'All perspectives acknowledge X',
                'There is consensus on Y',
                'Agreement exists regarding Z',
            ],
            'points_of_disagreement': [
                'Perspectives diverge on issue A',
                'Consensus breaks down on topic B',
                'Differing priorities regarding C',
            ],
            'synthesis': 'A holistic view integrating all perspectives suggests...',
        }


# ════════════════════════════════════════════════════════════════════════════
# INTEGRATED REASONING SYSTEM
# ════════════════════════════════════════════════════════════════════════════

class AdvancedReasoningSystem:
    """Complete advanced reasoning with debate & perspectives"""
    
    def __init__(self):
        self.debate_session = None
        self.questioner = SocraticQuestioner()
        self.advocate = DevilsAdvocate()
        self.analyzer = MultiPerspectiveAnalyzer()
        self.reasoning_history: List[Dict[str, Any]] = []
    
    async def debate_topic(self, topic: str, rounds: int = 3) -> Dict[str, Any]:
        """Run debate on topic"""
        self.debate_session = DebateSession(topic, rounds)
        result = await self.debate_session.conduct_debate()
        self.reasoning_history.append({
            'type': 'debate',
            'topic': topic,
            'timestamp': datetime.now().isoformat(),
            'result': result,
        })
        return result
    
    async def question_deeply(self, claim: str) -> Dict[str, Any]:
        """Ask Socratic questions"""
        questions = await self.questioner.generate_questions(claim)
        challenges = await self.questioner.challenge_assumption(claim)
        implications = await self.questioner.explore_implications(claim)
        
        result = {
            'claim': claim,
            'clarification_questions': questions,
            'assumption_challenges': challenges,
            'implication_questions': implications,
        }
        
        self.reasoning_history.append({
            'type': 'socratic_questioning',
            'claim': claim,
            'timestamp': datetime.now().isoformat(),
            'result': result,
        })
        
        return result
    
    async def challenge_position(self, position: str) -> Dict[str, Any]:
        """Generate devil's advocate"""
        opposition = await self.advocate.generate_opposition(position, 'strong')
        
        self.reasoning_history.append({
            'type': 'devils_advocate',
            'position': position,
            'timestamp': datetime.now().isoformat(),
            'result': opposition,
        })
        
        return opposition
    
    async def multi_perspective_analysis(self, question: str) -> Dict[str, Any]:
        """Analyze from multiple perspectives"""
        perspectives = await self.analyzer.analyze_from_perspectives(question)
        consensus = await self.analyzer.find_consensus(perspectives['perspectives'])
        
        result = {
            'question': question,
            'perspectives': perspectives['perspectives'],
            'consensus': consensus,
        }
        
        self.reasoning_history.append({
            'type': 'multi_perspective',
            'question': question,
            'timestamp': datetime.now().isoformat(),
            'result': result,
        })
        
        return result
    
    async def comprehensive_reasoning(self, topic: str) -> Dict[str, Any]:
        """Run all reasoning modes"""
        
        print(f"[Reasoning] Starting comprehensive reasoning on: {topic}")
        
        # 1. Debate
        print("  [1/4] Running debate...")
        debate = await self.debate_topic(topic, rounds=2)
        
        # 2. Socratic questions
        print("  [2/4] Generating Socratic questions...")
        socratic = await self.question_deeply(topic)
        
        # 3. Devil's advocate
        print("  [3/4] Generating opposition...")
        opposition = await self.challenge_position(topic)
        
        # 4. Multi-perspective
        print("  [4/4] Analyzing from multiple perspectives...")
        multi_persp = await self.multi_perspective_analysis(topic)
        
        return {
            'topic': topic,
            'debate': debate,
            'socratic_reasoning': socratic,
            'opposition': opposition,
            'multi_perspective': multi_persp,
            'total_reasoning_methods': 4,
        }


# ════════════════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════════════════

async def demo_reasoning_system():
    """Demonstrate reasoning system"""
    print("\n" + "="*70)
    print("ADVANCED: DEBATE & MULTI-PERSPECTIVE REASONING DEMO")
    print("="*70 + "\n")
    
    system = AdvancedReasoningSystem()
    
    topic = "Should AI systems be independently regulated?"
    
    # Run comprehensive reasoning
    result = await system.comprehensive_reasoning(topic)
    
    print(f"\n[Debate] Results:")
    print(f"  Stronger Position: {result['debate']['stronger_position'].upper()}")
    print(f"  Pro Strength: {result['debate']['pro_total_strength']:.2f}")
    print(f"  Con Strength: {result['debate']['con_total_strength']:.2f}")
    print(f"  Confidence: {result['debate']['confidence']:.1%}")
    
    print(f"\n[Socratic Reasoning] Key Questions:")
    for q in result['socratic_reasoning']['clarification_questions'][:3]:
        print(f"  • {q}")
    
    print(f"\n[Devil's Advocate] Opposition:")
    print(f"  {result['opposition']['opposition_statement']}")
    print(f"  Opposition Confidence: {result['opposition']['confidence']:.1%}")
    
    print(f"\n[Multi-Perspective] Perspectives Analyzed:")
    for perspective, data in result['multi_perspective']['perspectives'].items():
        print(f"  • {perspective.upper()}")
        print(f"    - Key Insight: {data['insights'][0]}")
        print(f"    - Main Concern: {data['concerns'][0]}")
    
    print(f"\n[Consensus] Analysis:")
    consensus = result['multi_perspective']['consensus']
    print(f"  Common Themes: {len(consensus['common_themes'])} identified")
    print(f"  Shared Concerns: {len(consensus['shared_concerns'])} identified")
    print(f"  Points of Agreement: {len(consensus['points_of_agreement'])}")
    print(f"  Points of Disagreement: {len(consensus['points_of_disagreement'])}")
    
    print(f"\n[Reasoning History] Total Reasoning Events: {len(system.reasoning_history)}")


if __name__ == "__main__":
    asyncio.run(demo_reasoning_system())
