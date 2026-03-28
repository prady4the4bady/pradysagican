"""
PHASE 10: FULL WORLD MODEL — TEST SUITE
Test environment simulation, state prediction, sensor integration, and imagination
"""

import pytest
from datetime import datetime

from pradysagican.consciousness.world_model import (
    EnvironmentState,
    SensoryInput,
    SensorType,
    ActionType,
    EnvironmentSimulator,
    StatePredictor,
    MultiSensoryIntegration,
    ImaginationEngine,
    initialize_world_model,
    demonstrate_world_model
)


class TestEnvironmentState:
    """Test environment state."""
    
    def test_create_state(self):
        """Test creating environment state."""
        state = EnvironmentState(
            timestamp=datetime.now().isoformat(),
            state_id="test_001",
            entities={"agent": {"position": [0, 0]}},
            relationships=[]
        )
        assert state.state_id == "test_001"
        assert "agent" in state.entities


class TestSensoryInput:
    """Test sensory input."""
    
    def test_create_sensory_input(self):
        """Test creating sensory input."""
        sensor = SensoryInput(
            sensor_type=SensorType.VISUAL,
            timestamp=datetime.now().isoformat(),
            data={"object": "detected"}
        )
        assert sensor.sensor_type == SensorType.VISUAL
        assert sensor.confidence == 1.0


class TestEnvironmentSimulator:
    """Test environment simulator."""
    
    def test_simulator_creation(self):
        """Test creating simulator."""
        sim = EnvironmentSimulator()
        assert sim.current_state is not None
        assert len(sim.history) == 1
    
    @pytest.mark.asyncio
    async def test_take_action(self):
        """Test taking action in simulator."""
        sim = EnvironmentSimulator()
        initial_pos = sim.current_state.entities["agent"]["position"]
        
        await sim.step(ActionType.MOVE, {"direction": [1, 0]})
        
        new_pos = sim.current_state.entities["agent"]["position"]
        assert new_pos[0] > initial_pos[0]
    
    @pytest.mark.asyncio
    async def test_multiple_steps(self):
        """Test multiple simulation steps."""
        sim = EnvironmentSimulator()
        
        for i in range(5):
            await sim.step(ActionType.MOVE, {"direction": [1, 1]})
        
        assert len(sim.history) == 6  # Initial + 5 steps
        assert sim.action_count == 5
    
    @pytest.mark.asyncio
    async def test_rollback(self):
        """Test rolling back simulation."""
        sim = EnvironmentSimulator()
        
        for i in range(3):
            await sim.step(ActionType.MOVE, {"direction": [1, 0]})
        
        state_before = sim.current_state
        await sim.rollback(1)
        state_after = sim.current_state
        
        assert state_before.state_id != state_after.state_id
    
    @pytest.mark.asyncio
    async def test_get_trajectory(self):
        """Test getting trajectory."""
        sim = EnvironmentSimulator()
        
        for i in range(3):
            await sim.step(ActionType.MOVE, {"direction": [1, 0]})
        
        trajectory = await sim.get_trajectory()
        assert len(trajectory) == 4


class TestStatePredictor:
    """Test state prediction."""
    
    def test_predictor_creation(self):
        """Test creating predictor."""
        predictor = StatePredictor()
        assert len(predictor.predictions) == 0
    
    @pytest.mark.asyncio
    async def test_predict_next_state(self):
        """Test predicting next state."""
        predictor = StatePredictor()
        
        state = EnvironmentState(
            timestamp=datetime.now().isoformat(),
            state_id="test_001",
            entities={"agent": {"position": [0, 0], "energy": 100}},
            relationships=[]
        )
        
        predicted = await predictor.predict_next_state(state, ActionType.MOVE, steps_ahead=1)
        
        assert predicted.state_id != state.state_id
        assert "pred" in predicted.state_id
    
    @pytest.mark.asyncio
    async def test_predict_trajectory(self):
        """Test predicting full trajectory."""
        predictor = StatePredictor()
        
        state = EnvironmentState(
            timestamp=datetime.now().isoformat(),
            state_id="traj_001",
            entities={"agent": {"position": [0, 0], "energy": 100}},
            relationships=[]
        )
        
        actions = [ActionType.MOVE, ActionType.MOVE, ActionType.MOVE]
        trajectory = await predictor.predict_trajectory(state, actions, num_predictions=5)
        
        assert len(trajectory) == len(actions) + 1
    
    @pytest.mark.asyncio
    async def test_score_accuracy(self):
        """Test scoring prediction accuracy."""
        predictor = StatePredictor()
        
        predicted = EnvironmentState(
            timestamp=datetime.now().isoformat(),
            state_id="pred_001",
            entities={"agent": {"position": [1, 1], "energy": 100}},
            relationships=[]
        )
        
        actual = EnvironmentState(
            timestamp=datetime.now().isoformat(),
            state_id="actual_001",
            entities={"agent": {"position": [1, 1], "energy": 100}},
            relationships=[]
        )
        
        accuracy = await predictor.score_prediction_accuracy(predicted, actual)
        assert 0 <= accuracy <= 1


class TestMultiSensoryIntegration:
    """Test sensory integration."""
    
    def test_integration_creation(self):
        """Test creating integration system."""
        integration = MultiSensoryIntegration()
        assert len(integration.sensor_weights) == 4
    
    @pytest.mark.asyncio
    async def test_integrate_sensors(self):
        """Test integrating multiple sensors."""
        integration = MultiSensoryIntegration()
        
        inputs = [
            SensoryInput(SensorType.VISUAL, datetime.now().isoformat(), 
                        {"object": 1.0, "distance": 5.0}),
            SensoryInput(SensorType.TEMPORAL, datetime.now().isoformat(),
                        {"time": 2.0})
        ]
        
        fused = await integration.integrate_sensors(inputs)
        
        assert "integrated_state" in fused
        assert fused["sensor_count"] == 2
    
    @pytest.mark.asyncio
    async def test_resolve_conflicts(self):
        """Test resolving conflicting sensors."""
        integration = MultiSensoryIntegration()
        
        inputs = [
            SensoryInput(SensorType.VISUAL, datetime.now().isoformat(),
                        {"distance": 5.0}, confidence=0.9),
            SensoryInput(SensorType.VISUAL, datetime.now().isoformat(),
                        {"distance": 4.0}, confidence=0.7)
        ]
        
        conflicts = await integration.resolve_conflicts(inputs)
        
        assert "visual" in conflicts
        assert conflicts["visual"]["confidence"] == 0.9


class TestImaginationEngine:
    """Test imagination engine."""
    
    def test_imagination_creation(self):
        """Test creating imagination engine."""
        engine = ImaginationEngine()
        assert engine.scenario_count == 0
    
    @pytest.mark.asyncio
    async def test_imagine_scenario(self):
        """Test imagining scenarios."""
        engine = ImaginationEngine()
        
        context = EnvironmentState(
            timestamp=datetime.now().isoformat(),
            state_id="context_001",
            entities={"agent": {"position": [0, 0], "energy": 100}, "goal": {"position": [10, 10]}},
            relationships=[]
        )
        
        goal = {"position": [10, 10]}
        scenarios = await engine.imagine_scenario(context, goal, num_branches=3)
        
        assert len(scenarios) == 3
        assert all("scenario_id" in s for s in scenarios)
    
    @pytest.mark.asyncio
    async def test_evaluate_imaginations(self):
        """Test evaluating imagined scenarios."""
        engine = ImaginationEngine()
        
        context = EnvironmentState(
            timestamp=datetime.now().isoformat(),
            state_id="eval_001",
            entities={"agent": {"position": [0, 0], "energy": 100}, "goal": {"position": [10, 10]}},
            relationships=[]
        )
        
        goal = {"position": [10, 10]}
        await engine.imagine_scenario(context, goal, num_branches=5)
        
        evaluation = await engine.evaluate_imaginations()
        
        assert "total_imagined" in evaluation
        assert "success_rate" in evaluation
        assert 0 <= evaluation["success_rate"] <= 1


class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.asyncio
    async def test_world_model_initialization(self):
        """Test initializing world model."""
        simulator, predictor, integration, imagination = await initialize_world_model()
        
        assert simulator is not None
        assert predictor is not None
        assert integration is not None
        assert imagination is not None
    
    @pytest.mark.asyncio
    async def test_demonstrate_world_model(self):
        """Test world model demonstration."""
        result = await demonstrate_world_model()
        
        assert "simulation_steps" in result
        assert "predictions_made" in result
        assert "sensors_integrated" in result
        assert "scenarios_imagined" in result
        assert result["simulation_steps"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
