"""
LAYER 6: Advanced Skills & Learning System
==========================================

Complete skill tree with 100+ capabilities, XP-based mastery,
meta-learning, and transfer learning.

Attribution: MMORPGs skill systems, meta-learning literature
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Set
from enum import Enum
import json

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════════
# SKILL SYSTEM
# ════════════════════════════════════════════════════════════════════════════

class SkillCategory(str, Enum):
    """Skill categories"""
    # Core domains
    REASONING = "reasoning"
    ANALYSIS = "analysis"
    CODING = "coding"
    PLANNING = "planning"
    
    # Technical
    DATA_SCIENCE = "data_science"
    WEB_DEVELOPMENT = "web_development"
    SYSTEMS_DESIGN = "systems_design"
    SECURITY = "security"
    
    # Soft skills
    COMMUNICATION = "communication"
    LEARNING = "learning"
    CREATIVITY = "creativity"
    DECISION_MAKING = "decision_making"
    
    # Domain expertise
    MATHEMATICS = "mathematics"
    PHYSICS = "physics"
    BIOLOGY = "biology"
    BUSINESS = "business"


@dataclass
class Skill:
    """Single skill with mastery tracking"""
    id: str
    name: str
    category: SkillCategory
    description: str
    xp: int = 0
    level: int = 1
    mastery: float = 0.0  # 0.0 to 1.0
    
    # Learning
    times_used: int = 0
    success_rate: float = 0.5
    last_used: Optional[datetime] = None
    
    # Prerequisites & relationships
    prerequisites: List[str] = field(default_factory=list)
    synergies: Dict[str, float] = field(default_factory=dict)  # Other skill -> bonus
    
    # Decay
    created_at: datetime = field(default_factory=datetime.now)
    decay_factor: float = 0.95  # 5% decay per week
    
    # Meta info
    difficulty: str = "medium"  # easy, medium, hard, expert
    hidden: bool = False
    requires_unlock: bool = False
    
    @property
    def is_maxed(self) -> bool:
        """Check if skill is maxed out"""
        return self.mastery >= 1.0
    
    @property
    def display_level(self) -> str:
        """Display level name"""
        if self.mastery >= 0.95:
            return "Master"
        elif self.mastery >= 0.80:
            return "Expert"
        elif self.mastery >= 0.60:
            return "Advanced"
        elif self.mastery >= 0.40:
            return "Intermediate"
        elif self.mastery >= 0.20:
            return "Novice"
        else:
            return "Apprentice"
    
    def gain_xp(self, amount: int, success: bool = True):
        """Add XP to skill"""
        self.xp += amount
        self.times_used += 1
        self.last_used = datetime.now()
        
        # Update mastery (capped at 1.0)
        self.mastery = min(1.0, self.xp / 1000.0)
        
        # Update level
        self.level = 1 + (self.xp // 100)
        
        # Update success rate
        if success:
            self.success_rate = (self.success_rate * (self.times_used - 1) + 1.0) / self.times_used
        else:
            self.success_rate = (self.success_rate * (self.times_used - 1)) / self.times_used
    
    def apply_decay(self):
        """Apply time-based decay (optional)"""
        weeks_old = (datetime.now() - self.created_at).days / 7
        decay_multiplier = self.decay_factor ** weeks_old
        self.mastery *= decay_multiplier


# ════════════════════════════════════════════════════════════════════════════
# SKILL TREE
# ════════════════════════════════════════════════════════════════════════════

class SkillTree:
    """
    Complete skill tree with 100+ skills,
    prerequisites, synergies, and progression
    """
    
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self.total_xp: int = 0
        self.level: int = 1
        self.specialization: Optional[str] = None
        self._initialize_skills()
    
    def _initialize_skills(self):
        """Initialize all 100+ skills"""
        
        # REASONING (15 skills)
        reasoning_skills = [
            ("logical_deduction", "Logical Deduction", "Break down logical problems"),
            ("lateral_thinking", "Lateral Thinking", "Think creatively outside the box"),
            ("pattern_recognition", "Pattern Recognition", "Identify patterns in data"),
            ("causal_inference", "Causal Inference", "Understand cause and effect"),
            ("counterfactual_reasoning", "Counterfactual Reasoning", "Reason about hypotheticals"),
            ("analogical_reasoning", "Analogical Reasoning", "Apply analogies between domains"),
            ("abductive_reasoning", "Abductive Reasoning", "Generate best explanations"),
            ("probabilistic_thinking", "Probabilistic Thinking", "Work with uncertainty"),
            ("game_theory", "Game Theory", "Analyze strategic interactions"),
            ("systems_thinking", "Systems Thinking", "Understand complex systems"),
            ("recursive_thinking", "Recursive Thinking", "Think recursively"),
            ("meta_reasoning", "Meta-Reasoning", "Reason about reasoning"),
            ("dialectical_thinking", "Dialectical Thinking", "Synthesize opposing views"),
            ("inductive_reasoning", "Inductive Reasoning", "Generalize from examples"),
            ("formal_logic", "Formal Logic", "Apply formal logical systems"),
        ]
        
        # ANALYSIS (15 skills)
        analysis_skills = [
            ("data_analysis", "Data Analysis", "Analyze data structures"),
            ("statistical_analysis", "Statistical Analysis", "Apply statistics"),
            ("trend_analysis", "Trend Analysis", "Identify trends"),
            ("root_cause_analysis", "Root Cause Analysis", "Find root causes"),
            ("comparative_analysis", "Comparative Analysis", "Compare options"),
            ("sentiment_analysis", "Sentiment Analysis", "Analyze sentiment"),
            ("network_analysis", "Network Analysis", "Analyze networks"),
            ("time_series_analysis", "Time Series Analysis", "Analyze temporal data"),
            ("anomaly_detection", "Anomaly Detection", "Detect anomalies"),
            ("clustering_analysis", "Clustering Analysis", "Group similar items"),
            ("regression_analysis", "Regression Analysis", "Model relationships"),
            ("competitive_analysis", "Competitive Analysis", "Analyze competitors"),
            ("market_analysis", "Market Analysis", "Analyze markets"),
            ("risk_analysis", "Risk Analysis", "Assess risks"),
            ("cost_benefit_analysis", "Cost-Benefit Analysis", "Compare costs vs benefits"),
        ]
        
        # CODING (20 skills)
        coding_skills = [
            ("python_programming", "Python Programming", "Write Python code"),
            ("javascript_programming", "JavaScript Programming", "Write JavaScript"),
            ("java_programming", "Java Programming", "Write Java code"),
            ("cpp_programming", "C++ Programming", "Write C++ code"),
            ("rust_programming", "Rust Programming", "Write Rust code"),
            ("web_development", "Web Development", "Build web apps"),
            ("backend_development", "Backend Development", "Build backends"),
            ("frontend_development", "Frontend Development", "Build frontends"),
            ("database_design", "Database Design", "Design databases"),
            ("api_design", "API Design", "Design APIs"),
            ("system_architecture", "System Architecture", "Design systems"),
            ("refactoring", "Refactoring", "Improve code"),
            ("testing", "Testing", "Write tests"),
            ("debugging", "Debugging", "Debug code"),
            ("code_review", "Code Review", "Review code"),
            ("performance_optimization", "Performance Optimization", "Optimize code"),
            ("security_programming", "Security Programming", "Write secure code"),
            ("devops", "DevOps", "Deploy systems"),
            ("containerization", "Containerization", "Use containers"),
            ("microservices", "Microservices", "Build microservices"),
        ]
        
        # PLANNING (15 skills)
        planning_skills = [
            ("project_planning", "Project Planning", "Plan projects"),
            ("timeline_estimation", "Timeline Estimation", "Estimate timelines"),
            ("resource_allocation", "Resource Allocation", "Allocate resources"),
            ("risk_management", "Risk Management", "Manage risks"),
            ("stakeholder_management", "Stakeholder Management", "Manage stakeholders"),
            ("prioritization", "Prioritization", "Prioritize tasks"),
            ("goal_setting", "Goal Setting", "Set effective goals"),
            ("milestone_tracking", "Milestone Tracking", "Track milestones"),
            ("agile_methodology", "Agile Methodology", "Use Agile"),
            ("scrum_master", "Scrum Master", "Facilitate Scrum"),
            ("kanban", "Kanban", "Use Kanban"),
            ("lean_management", "Lean Management", "Apply Lean"),
            ("strategy_formulation", "Strategy Formulation", "Formulate strategy"),
            ("execution_planning", "Execution Planning", "Plan execution"),
            ("contingency_planning", "Contingency Planning", "Plan for contingencies"),
        ]
        
        # DATA SCIENCE (20 skills)
        data_science_skills = [
            ("machine_learning", "Machine Learning", "Apply ML algorithms"),
            ("deep_learning", "Deep Learning", "Build neural networks"),
            ("nlp", "Natural Language Processing", "Process text"),
            ("computer_vision", "Computer Vision", "Process images"),
            ("reinforcement_learning", "Reinforcement Learning", "Apply RL"),
            ("feature_engineering", "Feature Engineering", "Engineer features"),
            ("model_evaluation", "Model Evaluation", "Evaluate models"),
            ("hyperparameter_tuning", "Hyperparameter Tuning", "Tune hyperparameters"),
            ("cross_validation", "Cross Validation", "Use cross validation"),
            ("ensemble_methods", "Ensemble Methods", "Combine models"),
            ("time_series_forecasting", "Time Series Forecasting", "Forecast time series"),
            ("anomaly_detection_ml", "Anomaly Detection (ML)", "Detect anomalies with ML"),
            ("recommendation_systems", "Recommendation Systems", "Build recommenders"),
            ("knowledge_graphs", "Knowledge Graphs", "Build knowledge graphs"),
            ("transfer_learning", "Transfer Learning", "Transfer knowledge"),
            ("few_shot_learning", "Few-Shot Learning", "Learn from few examples"),
            ("meta_learning", "Meta-Learning", "Learn to learn"),
            ("federated_learning", "Federated Learning", "Learn on distributed data"),
            ("active_learning", "Active Learning", "Learn actively"),
            ("interpretability", "Interpretability", "Interpret models"),
        ]
        
        # Additional domain skills (15)
        domain_skills = [
            ("mathematics", "Mathematics", "Advanced mathematics"),
            ("physics", "Physics", "Understand physics"),
            ("business_acumen", "Business Acumen", "Understand business"),
            ("psychology", "Psychology", "Understand psychology"),
            ("communication", "Communication", "Communicate effectively"),
            ("negotiation", "Negotiation", "Negotiate effectively"),
            ("leadership", "Leadership", "Lead teams"),
            ("creativity", "Creativity", "Think creatively"),
            ("decision_making", "Decision Making", "Make good decisions"),
            ("research", "Research", "Conduct research"),
            ("writing", "Writing", "Write well"),
            ("presentation", "Presentation", "Present effectively"),
            ("problem_solving", "Problem Solving", "Solve problems"),
            ("innovation", "Innovation", "Drive innovation"),
            ("continuous_learning", "Continuous Learning", "Keep learning"),
        ]
        
        # Create all skills
        all_skills = (
            [(s[0], s[1], SkillCategory.REASONING, s[2]) for s in reasoning_skills] +
            [(s[0], s[1], SkillCategory.ANALYSIS, s[2]) for s in analysis_skills] +
            [(s[0], s[1], SkillCategory.CODING, s[2]) for s in coding_skills] +
            [(s[0], s[1], SkillCategory.PLANNING, s[2]) for s in planning_skills] +
            [(s[0], s[1], SkillCategory.DATA_SCIENCE, s[2]) for s in data_science_skills] +
            [(s[0], s[1], SkillCategory.BUSINESS, s[2]) for s in domain_skills]
        )
        
        for skill_id, name, category, description in all_skills:
            skill = Skill(
                id=skill_id,
                name=name,
                category=category,
                description=description,
                difficulty="medium"
            )
            self.skills[skill_id] = skill
        
        # Add synergies
        self._add_synergies()
    
    def _add_synergies(self):
        """Add skill synergies (bonus when using together)"""
        synergies = [
            ("logical_deduction", "pattern_recognition", 0.15),
            ("causal_inference", "counterfactual_reasoning", 0.20),
            ("python_programming", "data_analysis", 0.25),
            ("machine_learning", "statistics", 0.30),
            ("system_architecture", "database_design", 0.20),
            ("nlp", "sentiment_analysis", 0.25),
            ("leadership", "communication", 0.25),
            ("creative_thinking", "innovation", 0.30),
        ]
        
        for skill1, skill2, bonus in synergies:
            if skill1 in self.skills and skill2 in self.skills:
                if skill2 not in self.skills[skill1].synergies:
                    self.skills[skill1].synergies[skill2] = bonus
    
    async def use_skill(self, skill_id: str, xp_gained: int = 10, 
                       success: bool = True, with_synergy: str = None) -> Dict[str, Any]:
        """Use a skill and gain experience"""
        if skill_id not in self.skills:
            return {'success': False, 'error': f'Skill {skill_id} not found'}
        
        skill = self.skills[skill_id]
        base_xp = xp_gained
        
        # Apply synergy bonus if another skill is used
        if with_synergy and with_synergy in skill.synergies:
            bonus = skill.synergies[with_synergy]
            xp_gained = int(xp_gained * (1 + bonus))
        
        skill.gain_xp(xp_gained, success)
        self.total_xp += xp_gained
        self.level = 1 + (self.total_xp // 500)
        
        return {
            'success': True,
            'skill_id': skill_id,
            'skill_name': skill.name,
            'xp_gained': xp_gained,
            'total_xp': skill.xp,
            'level': skill.level,
            'mastery': skill.mastery,
            'display_level': skill.display_level,
        }
    
    async def get_skill_stats(self) -> Dict[str, Any]:
        """Get overall skill stats"""
        skills_by_category = {}
        for category in SkillCategory:
            skills = [s for s in self.skills.values() if s.category == category]
            avg_mastery = sum(s.mastery for s in skills) / len(skills) if skills else 0
            skills_by_category[category.value] = {
                'count': len(skills),
                'avg_mastery': avg_mastery,
                'maxed': len([s for s in skills if s.is_maxed])
            }
        
        return {
            'total_skills': len(self.skills),
            'total_xp': self.total_xp,
            'level': self.level,
            'by_category': skills_by_category,
            'specialization': self.specialization
        }
    
    async def get_top_skills(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top mastered skills"""
        sorted_skills = sorted(
            self.skills.values(),
            key=lambda s: s.mastery,
            reverse=True
        )
        
        return [
            {
                'id': s.id,
                'name': s.name,
                'category': s.category.value,
                'mastery': s.mastery,
                'level': s.level,
                'display_level': s.display_level,
                'times_used': s.times_used,
                'success_rate': s.success_rate,
            }
            for s in sorted_skills[:limit]
        ]
    
    async def recommend_next_skills(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Recommend skills to learn next"""
        # Find skills with high synergy to currently mastered skills
        recommendations = []
        
        for skill_id, skill in self.skills.items():
            if skill.mastery < 0.3:  # Not yet learned
                # Check synergy score
                synergy_score = 0
                for other_id, bonus in skill.synergies.items():
                    if other_id in self.skills:
                        other_mastery = self.skills[other_id].mastery
                        synergy_score += bonus * other_mastery
                
                recommendations.append({
                    'id': skill_id,
                    'name': skill.name,
                    'category': skill.category.value,
                    'synergy_score': synergy_score,
                    'difficulty': skill.difficulty,
                })
        
        # Sort by synergy score
        recommendations.sort(key=lambda r: r['synergy_score'], reverse=True)
        return recommendations[:limit]


# ════════════════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════════════════

async def demo_skill_system():
    """Demonstrate skill learning system"""
    print("\n" + "="*70)
    print("LAYER 6: ADVANCED SKILLS & LEARNING SYSTEM DEMO")
    print("="*70 + "\n")
    
    tree = SkillTree()
    
    print(f"[Skills] Initialized skill tree with {len(tree.skills)} skills")
    
    # Simulate learning journey
    learning_path = [
        ("pattern_recognition", 50, True),
        ("logical_deduction", 40, True),
        ("data_analysis", 60, True),
        ("python_programming", 100, True),
        ("machine_learning", 80, True),
        ("machine_learning", 50, True),  # Learn again
        ("deep_learning", 100, True),
    ]
    
    print("\n[Learning] Simulating learning journey...\n")
    
    for skill_id, xp, success in learning_path:
        result = await tree.use_skill(skill_id, xp_gained=xp, success=success)
        if result['success']:
            print(f"  [+] {result['skill_name']:25} +{result['xp_gained']:3d} XP -> "
                  f"Level {result['level']:2d} ({result['display_level']:10s})")
    
    # Show stats
    print("\n[Stats] Skill progression:")
    stats = await tree.get_skill_stats()
    print(f"  Total XP: {stats['total_xp']:,}")
    print(f"  Overall Level: {stats['level']}")
    
    print("\n[Skills] Top 10 mastered skills:")
    top_skills = await tree.get_top_skills(10)
    for i, skill in enumerate(top_skills, 1):
        print(f"  {i:2d}. {skill['name']:30s} {skill['display_level']:10s} "
              f"({skill['mastery']*100:5.1f}%)")
    
    print("\n[Recommendations] Suggested next skills:")
    recommendations = await tree.recommend_next_skills(5)
    for rec in recommendations:
        print(f"  • {rec['name']:30s} (Synergy: {rec['synergy_score']:.2f})")
    
    print("\n[Stats] By category:")
    for cat, info in stats['by_category'].items():
        print(f"  {cat:20s}: {info['avg_mastery']*100:5.1f}% avg mastery "
              f"({info['maxed']} maxed)")


if __name__ == "__main__":
    asyncio.run(demo_skill_system())
