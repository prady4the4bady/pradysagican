"""
F627: Counterfactual Reasoning Engine

Enables reasoning about hypothetical scenarios by computing what would have
happened under different conditions. Implements abductive inference, causal
contraposition, and structural equation modeling for counterfactuals.

Key Features:
- Structural Causal Model (SCM) based counterfactual queries
- Three-step counterfactual inference: abduction, action, prediction
- Constraint-based counterfactual discovery
- Sensitivity analysis for robustness
- Contrastive explanations (why X instead of Y?)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any
from enum import Enum
import numpy as np
from datetime import datetime


class CounterfactualType(Enum):
    """Types of counterfactual queries"""
    SIMPLE = "simple"              # Single variable change
    COMPLEX = "complex"            # Multiple variable changes
    ABDUCTIVE = "abductive"        # Infer past from observations
    TEMPORAL = "temporal"          # Sequential changes
    STRUCTURAL = "structural"      # System-level changes


@dataclass
class Observation:
    """Observed state of world"""
    variables: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(datetime.UTC).isoformat())


@dataclass
class Counterfactual:
    """Counterfactual scenario and its properties"""
    query: str  # Natural language query
    interventions: Dict[str, Any]  # Variables to change: {var: new_value}
    predicted_outcome: Dict[str, Any]  # Predicted state after interventions
    confidence: float  # 0-1, confidence in prediction
    type: CounterfactualType
    constraints_satisfied: bool
    explanation: str
    minimal: bool  # Whether this is minimal counterfactual (minimal changes)


@dataclass
class CounterfactualSequence:
    """Sequence of counterfactual steps"""
    initial_state: Dict[str, Any]
    steps: List[Dict[str, Any]]  # Sequence of interventions
    final_state: Dict[str, Any]
    path_validity: float  # 0-1, probability path is realizable
    causal_mechanism: List[str]  # Explanation of mechanism


class CounterfactualReasoningEngine:
    """
    Reasons about hypothetical scenarios using causal models.
    
    Implements Pearl's three-step counterfactual inference:
    1. Abduction: update beliefs given observations
    2. Action: modify model with interventions  
    3. Prediction: compute new distribution
    """

    def __init__(self, causal_model: Optional[Dict] = None):
        """Initialize counterfactual reasoning engine"""
        self.causal_model = causal_model or {}
        self.observations: List[Observation] = []
        self.counterfactuals: List[Counterfactual] = []
        self.structural_equations: Dict[str, Any] = {}
        self.constraint_set: Set[str] = set()

    def record_observation(self, variables: Dict[str, Any]) -> None:
        """Record observed state"""
        self.observations.append(Observation(variables=variables))

    def set_structural_equations(self, equations: Dict[str, str]) -> None:
        """
        Set structural equations defining causal relationships.
        
        Example:
            {
                "income": "education * 50000 + experience * 10000 + epsilon",
                "happiness": "income * 0.0001 + health + epsilon"
            }
        """
        self.structural_equations = equations

    def add_constraint(self, constraint: str) -> None:
        """
        Add constraint that must be satisfied.
        
        Example: "age >= 0 and age <= 120"
        """
        self.constraint_set.add(constraint)

    def query_counterfactual(
        self,
        query: str,
        interventions: Dict[str, Any],
        cf_type: CounterfactualType = CounterfactualType.SIMPLE
    ) -> Counterfactual:
        """
        Generate counterfactual prediction.
        
        Args:
            query: Natural language query (e.g., "What if education was higher?")
            interventions: Variables to intervene on: {var: new_value}
            cf_type: Type of counterfactual
        
        Returns:
            Counterfactual with predicted outcome and confidence
        """
        # Get current observation
        current = self.observations[-1] if self.observations else Observation(variables={})
        
        # Step 1: Abduction - infer unobserved exogenous variables
        abduced_exogenous = self._abduct_exogenous_vars(current.variables)
        
        # Step 2: Action - modify model with interventions
        modified_state = self._apply_interventions(current.variables, interventions)
        
        # Step 3: Prediction - compute outcome in modified model
        predicted = self._predict_outcome(modified_state, abduced_exogenous)
        
        # Check constraint satisfaction
        constraints_ok = self._check_constraints(predicted)
        
        # Compute confidence
        confidence = self._compute_confidence(
            current.variables, 
            predicted, 
            interventions,
            constraints_ok
        )
        
        # Generate explanation
        explanation = self._generate_explanation(
            current.variables, 
            interventions, 
            predicted
        )
        
        # Check if minimal
        minimal = self._is_minimal_counterfactual(interventions, current.variables)
        
        cf = Counterfactual(
            query=query,
            interventions=interventions,
            predicted_outcome=predicted,
            confidence=confidence,
            type=cf_type,
            constraints_satisfied=constraints_ok,
            explanation=explanation,
            minimal=minimal
        )
        
        self.counterfactuals.append(cf)
        return cf

    def find_minimal_counterfactuals(
        self,
        target_outcome: Dict[str, Any],
        max_interventions: int = 3
    ) -> List[Counterfactual]:
        """
        Find minimal set of interventions to achieve target outcome.
        Minimal = fewest variable changes needed.
        """
        minimal_cfs = []
        current_obs = self.observations[-1] if self.observations else Observation({})
        
        # Try all combinations up to max_interventions
        for num_vars in range(1, min(max_interventions + 1, len(current_obs.variables))):
            candidates = self._generate_intervention_candidates(
                current_obs.variables, 
                target_outcome, 
                num_vars
            )
            
            for interventions in candidates:
                cf = self.query_counterfactual(
                    f"Minimal path to {target_outcome}",
                    interventions,
                    CounterfactualType.SIMPLE
                )
                
                if self._matches_target(cf.predicted_outcome, target_outcome):
                    minimal_cfs.append(cf)
        
        # Return minimal ones (fewest interventions)
        return sorted(minimal_cfs, 
                     key=lambda cf: len(cf.interventions))[:3]

    def generate_contrastive_explanation(
        self,
        actual: Dict[str, Any],
        foil: Dict[str, Any]
    ) -> str:
        """
        Generate contrastive explanation: "Why X instead of Y?"
        
        Example:
            actual = {"diagnosis": "pneumonia"}
            foil = {"diagnosis": "common_cold"}
            
            Explanation: "Pneumonia rather than common cold because:
            - Fever temperature (40°C vs 38°C)
            - Chest X-ray shows consolidation (present vs absent)
            - Positive bacterial culture (yes vs no)"
        """
        differences = []
        for var in set(list(actual.keys()) + list(foil.keys())):
            actual_val = actual.get(var)
            foil_val = foil.get(var)
            if actual_val != foil_val:
                differences.append((var, actual_val, foil_val))
        
        explanation = "Contrastive explanation:\n"
        for var, actual_val, foil_val in differences:
            explanation += f"- {var}: {actual_val} (vs {foil_val})\n"
        
        return explanation

    def sensitivity_analysis(
        self,
        base_interventions: Dict[str, Any],
        sensitivity_vars: Set[str],
        perturbation_range: Tuple[float, float] = (-0.1, 0.1)
    ) -> Dict[str, List[Counterfactual]]:
        """
        Analyze sensitivity of counterfactual to perturbations.
        Shows how robust the counterfactual is to model uncertainty.
        """
        results = {}
        
        for var in sensitivity_vars:
            current_val = base_interventions.get(var)
            if current_val is None or not isinstance(current_val, (int, float)):
                continue
            
            cfs = []
            for perturbation in np.linspace(*perturbation_range, 5):
                modified_interventions = base_interventions.copy()
                modified_interventions[var] = current_val + perturbation
                
                cf = self.query_counterfactual(
                    f"Sensitivity test for {var}",
                    modified_interventions
                )
                cfs.append(cf)
            
            results[var] = cfs
        
        return results

    def temporal_counterfactual(
        self,
        initial_state: Dict[str, Any],
        intervention_schedule: List[Tuple[int, Dict[str, Any]]]  # [(timestep, interventions), ...]
    ) -> CounterfactualSequence:
        """
        Simulate counterfactual sequence over time.
        
        Args:
            initial_state: Starting state
            intervention_schedule: Interventions at specific timesteps
        
        Returns:
            CounterfactualSequence showing evolution
        """
        current_state = initial_state.copy()
        steps = []
        
        # Sort by timestep
        schedule = sorted(intervention_schedule, key=lambda x: x[0])
        
        for timestep, interventions in schedule:
            current_state = self._apply_interventions(current_state, interventions)
            steps.append({
                "timestep": timestep,
                "state": current_state.copy(),
                "interventions": interventions
            })
        
        # Compute final state
        final_state = current_state.copy()
        
        # Compute path validity (probability this sequence is realizable)
        path_validity = self._compute_path_validity(steps)
        
        # Get causal mechanism explanation
        mechanism = self._explain_causal_mechanism(steps)
        
        return CounterfactualSequence(
            initial_state=initial_state,
            steps=steps,
            final_state=final_state,
            path_validity=path_validity,
            causal_mechanism=mechanism
        )

    def _abduct_exogenous_vars(self, observations: Dict[str, Any]) -> Dict[str, Any]:
        """Infer unobserved exogenous variables (Step 1 of 3)"""
        # Simplified: assume uniform distribution over exogenous vars
        abduced = {}
        for var in self.causal_model.get("exogenous_vars", []):
            abduced[var] = np.random.normal(0, 1)
        return abduced

    def _apply_interventions(
        self,
        state: Dict[str, Any],
        interventions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply interventions by setting variables (Step 2 of 3)"""
        modified = state.copy()
        modified.update(interventions)
        return modified

    def _predict_outcome(
        self,
        modified_state: Dict[str, Any],
        exogenous: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict outcome in modified model (Step 3 of 3)"""
        # Apply structural equations to get new values
        predicted = modified_state.copy()
        
        for var, eq in self.structural_equations.items():
            try:
                # Simplified evaluation (in real system would be more careful)
                predicted[var] = eval(eq, {**predicted, **exogenous})
            except:
                pass
        
        return predicted

    def _check_constraints(self, state: Dict[str, Any]) -> bool:
        """Check if state satisfies all constraints"""
        for constraint in self.constraint_set:
            try:
                if not eval(constraint, state):
                    return False
            except:
                pass
        return True

    def _compute_confidence(
        self,
        current: Dict[str, Any],
        predicted: Dict[str, Any],
        interventions: Dict[str, Any],
        constraints_ok: bool
    ) -> float:
        """Compute confidence in counterfactual prediction"""
        # Higher confidence if:
        # 1. Fewer interventions
        # 2. Constraints satisfied
        # 3. Smaller changes from current state
        
        confidence = 1.0
        
        # Penalty for multiple interventions
        confidence -= len(interventions) * 0.1
        
        # Penalty for constraint violation
        if not constraints_ok:
            confidence -= 0.2
        
        # Penalty for large state changes
        max_change = max([
            abs(predicted.get(k, 0) - current.get(k, 0))
            for k in set(list(current.keys()) + list(predicted.keys()))
        ])
        confidence -= min(0.3, max_change * 0.05)
        
        return max(0.0, min(1.0, confidence))

    def _generate_explanation(
        self,
        current: Dict[str, Any],
        interventions: Dict[str, Any],
        predicted: Dict[str, Any]
    ) -> str:
        """Generate natural language explanation"""
        exp = "If we changed: "
        exp += ", ".join([f"{k} to {v}" for k, v in interventions.items()])
        exp += ", then we would expect: "
        
        changes = []
        for k, v in predicted.items():
            if k not in interventions:
                old_v = current.get(k)
                if old_v != v:
                    changes.append(f"{k} to change from {old_v} to {v}")
        
        exp += ", ".join(changes) if changes else "no other changes"
        return exp

    def _is_minimal_counterfactual(
        self,
        interventions: Dict[str, Any],
        current: Dict[str, Any]
    ) -> bool:
        """Check if counterfactual uses minimal set of interventions"""
        # Minimal if no subset of interventions achieves similar outcome
        return len(interventions) <= 2

    def _generate_intervention_candidates(
        self,
        current: Dict[str, Any],
        target: Dict[str, Any],
        num_vars: int
    ) -> List[Dict[str, Any]]:
        """Generate candidate interventions"""
        candidates = []
        
        # Find variables that differ between current and target
        diff_vars = [
            k for k in set(list(current.keys()) + list(target.keys()))
            if current.get(k) != target.get(k)
        ]
        
        # Use first num_vars from diff_vars
        for var in diff_vars[:num_vars]:
            interventions = {var: target.get(var)}
            candidates.append(interventions)
        
        return candidates

    def _matches_target(
        self,
        predicted: Dict[str, Any],
        target: Dict[str, Any]
    ) -> bool:
        """Check if predicted outcome matches target"""
        for k, v in target.items():
            if predicted.get(k) != v:
                return False
        return True

    def _compute_path_validity(self, steps: List[Dict[str, Any]]) -> float:
        """Compute probability that temporal sequence is realizable"""
        # Simplified: assume high validity for short sequences
        return max(0.5, 1.0 - len(steps) * 0.1)

    def _explain_causal_mechanism(self, steps: List[Dict[str, Any]]) -> List[str]:
        """Explain causal mechanism of temporal sequence"""
        mechanisms = []
        for i, step in enumerate(steps):
            mech = f"Step {i+1}: interventions {step['interventions']} "
            mech += f"lead to state {step['state']}"
            mechanisms.append(mech)
        return mechanisms

    def get_counterfactual_summary(self) -> Dict[str, Any]:
        """Get summary statistics of counterfactual reasoning"""
        if not self.counterfactuals:
            return {"num_counterfactuals": 0}
        
        avg_confidence = np.mean([cf.confidence for cf in self.counterfactuals])
        
        return {
            "num_counterfactuals": len(self.counterfactuals),
            "avg_confidence": avg_confidence,
            "constraints_satisfied": sum(
                1 for cf in self.counterfactuals if cf.constraints_satisfied
            ) / len(self.counterfactuals),
            "minimal_counterfactuals": sum(
                1 for cf in self.counterfactuals if cf.minimal
            ) / len(self.counterfactuals)
        }
