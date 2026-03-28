#!/usr/bin/env python3
"""
PHASE 17: MULTI-MODAL EMBODIMENT
Embodied AI with multiple sensing and actuation modalities
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class SensorType(Enum):
    """Types of sensors"""
    VISION = "vision"
    AUDIO = "audio"
    PROPRIOCEPTION = "proprioception"
    TOUCH = "touch"
    CHEMICAL = "chemical"


class ActuatorType(Enum):
    """Types of actuators"""
    MOTOR = "motor"
    SPEECH = "speech"
    DISPLAY = "display"
    MANIPULATION = "manipulation"
    NAVIGATION = "navigation"


@dataclass
class SensorReading:
    """Single sensor reading"""
    sensor_id: str
    sensor_type: SensorType
    data: float
    confidence: float
    timestamp: int


@dataclass
class MotorCommand:
    """Command to actuator"""
    actuator_id: str
    actuator_type: ActuatorType
    intensity: float           # 0-1
    duration_ms: int
    precision: float


class SensoryProcessor:
    """Processes multimodal sensory input"""
    
    def __init__(self):
        self.sensors: Dict[str, SensorType] = {}
        self.readings: List[SensorReading] = []
        self.sensory_fusion: Dict[str, float] = {}
        self.attention_weights: Dict[SensorType, float] = {st: 0.2 for st in SensorType}
    
    async def register_sensor(self, sensor_id: str, sensor_type: SensorType) -> None:
        """Register sensor"""
        self.sensors[sensor_id] = sensor_type
    
    async def process_reading(self, reading: SensorReading) -> None:
        """Process sensor reading"""
        self.readings.append(reading)
        
        # Update sensory fusion
        sensor_type = reading.sensor_type
        if sensor_type not in self.sensory_fusion:
            self.sensory_fusion[sensor_type.value] = 0.0
        
        # Weighted update
        self.sensory_fusion[sensor_type.value] = (
            0.7 * self.sensory_fusion[sensor_type.value] + 
            0.3 * reading.data * reading.confidence
        )
    
    async def dynamic_attention(self) -> None:
        """Dynamically adjust attention to modalities"""
        
        # Increase attention to high-activity modalities
        for sensor_type in SensorType:
            readings_of_type = [r for r in self.readings[-10:] if r.sensor_type == sensor_type]
            
            if readings_of_type:
                avg_signal = sum(r.data for r in readings_of_type) / len(readings_of_type)
                
                # Increase attention if signal is high
                if avg_signal > 0.5:
                    self.attention_weights[sensor_type] = min(
                        1.0,
                        self.attention_weights[sensor_type] + 0.1
                    )
                else:
                    self.attention_weights[sensor_type] = max(
                        0.1,
                        self.attention_weights[sensor_type] - 0.05
                    )
    
    async def get_fused_perception(self) -> Dict[str, float]:
        """Get fused multimodal perception"""
        
        fused = {}
        total_weight = sum(self.attention_weights.values())
        
        for sensor_type, reading_value in self.sensory_fusion.items():
            # Find matching sensor type
            for st in SensorType:
                if st.value == sensor_type:
                    weight = self.attention_weights[st] / total_weight
                    fused[sensor_type] = reading_value * weight
                    break
        
        return fused


class MotorController:
    """Controls motor actions"""
    
    def __init__(self):
        self.actuators: Dict[str, ActuatorType] = {}
        self.commands: List[MotorCommand] = []
        self.execution_history: List[Dict] = []
    
    async def register_actuator(self, actuator_id: str, actuator_type: ActuatorType) -> None:
        """Register actuator"""
        self.actuators[actuator_id] = actuator_type
    
    async def execute_command(self, command: MotorCommand) -> Dict:
        """Execute motor command"""
        
        self.commands.append(command)
        
        # Simulate execution
        success = command.precision > 0.7
        
        execution = {
            'command': command.actuator_id,
            'type': command.actuator_type.value,
            'intensity': command.intensity,
            'success': success,
            'actual_intensity': command.intensity if success else command.intensity * 0.7
        }
        
        self.execution_history.append(execution)
        
        return execution
    
    async def parallel_execute(self, commands: List[MotorCommand]) -> List[Dict]:
        """Execute multiple commands in parallel"""
        
        results = []
        for cmd in commands:
            result = await self.execute_command(cmd)
            results.append(result)
        
        return results
    
    async def get_motor_state(self) -> Dict:
        """Get current motor state"""
        
        return {
            'total_actuators': len(self.actuators),
            'commands_executed': len(self.commands),
            'successful_executions': sum(1 for e in self.execution_history if e['success']),
            'success_rate': (
                sum(1 for e in self.execution_history if e['success']) / 
                len(self.execution_history) if self.execution_history else 0
            )
        }


class EmbodiedAgent:
    """Embodied agent with sensors and actuators"""
    
    def __init__(self):
        self.sensory_processor = SensoryProcessor()
        self.motor_controller = MotorController()
        self.body_state: Dict = {}
        self.interaction_log: List[Dict] = []
    
    async def initialize_embodiment(self) -> None:
        """Initialize sensors and actuators"""
        
        # Register sensors
        sensor_configs = [
            ("vision_1", SensorType.VISION),
            ("audio_1", SensorType.AUDIO),
            ("proprioception_1", SensorType.PROPRIOCEPTION),
            ("touch_1", SensorType.TOUCH),
        ]
        
        for sensor_id, sensor_type in sensor_configs:
            await self.sensory_processor.register_sensor(sensor_id, sensor_type)
        
        # Register actuators
        actuator_configs = [
            ("motor_arm", ActuatorType.MOTOR),
            ("motor_leg", ActuatorType.MOTOR),
            ("speech_vocal", ActuatorType.SPEECH),
            ("display_screen", ActuatorType.DISPLAY),
        ]
        
        for actuator_id, actuator_type in actuator_configs:
            await self.motor_controller.register_actuator(actuator_id, actuator_type)
    
    async def sense_environment(self) -> Dict[str, float]:
        """Perceive environment through all senses"""
        
        import random
        import time
        
        timestamp = int(time.time() * 1000)
        
        # Generate readings from each sensor
        for sensor_id, sensor_type in self.sensory_processor.sensors.items():
            data = random.random()
            confidence = 0.7 + random.random() * 0.3
            
            reading = SensorReading(
                sensor_id=sensor_id,
                sensor_type=sensor_type,
                data=data,
                confidence=confidence,
                timestamp=timestamp
            )
            
            await self.sensory_processor.process_reading(reading)
        
        # Update attention
        await self.sensory_processor.dynamic_attention()
        
        # Get fused perception
        fused = await self.sensory_processor.get_fused_perception()
        
        return fused
    
    async def act_on_world(self, intention: str) -> List[Dict]:
        """Execute action based on intention"""
        
        commands = []
        
        # Generate motor commands based on intention
        if "move" in intention:
            commands.append(MotorCommand(
                actuator_id="motor_leg",
                actuator_type=ActuatorType.MOTOR,
                intensity=0.8,
                duration_ms=1000,
                precision=0.9
            ))
        
        if "speak" in intention:
            commands.append(MotorCommand(
                actuator_id="speech_vocal",
                actuator_type=ActuatorType.SPEECH,
                intensity=0.7,
                duration_ms=2000,
                precision=0.85
            ))
        
        if "manipulate" in intention:
            commands.append(MotorCommand(
                actuator_id="motor_arm",
                actuator_type=ActuatorType.MOTOR,
                intensity=0.6,
                duration_ms=500,
                precision=0.95
            ))
        
        # Execute commands
        if commands:
            results = await self.motor_controller.parallel_execute(commands)
            return results
        
        return []
    
    async def interaction_cycle(self, num_cycles: int = 3) -> List[Dict]:
        """Run complete sense-think-act cycle"""
        
        cycle_results = []
        
        for cycle in range(num_cycles):
            # Sense
            perception = await self.sense_environment()
            
            # Think (decide action)
            intentions = []
            if perception.get('vision', 0) > 0.5:
                intentions.append("move")
            if perception.get('audio', 0) > 0.6:
                intentions.append("speak")
            if perception.get('touch', 0) > 0.7:
                intentions.append("manipulate")
            
            # Act
            actions = []
            for intention in intentions:
                action_results = await self.act_on_world(intention)
                actions.extend(action_results)
            
            cycle_result = {
                'cycle': cycle,
                'perception': perception,
                'intentions': intentions,
                'actions': len(actions),
                'success_rate': (
                    sum(1 for a in actions if a['success']) / len(actions)
                    if actions else 0
                )
            }
            
            cycle_results.append(cycle_result)
            self.interaction_log.append(cycle_result)
        
        return cycle_results
    
    async def get_embodiment_state(self) -> Dict:
        """Get complete embodiment state"""
        
        motor_state = await self.motor_controller.get_motor_state()
        
        return {
            'sensors_registered': len(self.sensory_processor.sensors),
            'actuators_registered': len(self.motor_controller.actuators),
            'sensory_readings': len(self.sensory_processor.readings),
            'motor_commands': motor_state,
            'interaction_cycles': len(self.interaction_log),
            'total_actions': sum(c.get('actions', 0) for c in self.interaction_log),
        }


# ════════════════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════════════════

async def demo_embodied_agent():
    """Demonstrate embodied AI"""
    
    print("\n" + "=" * 70)
    print("MULTI-MODAL EMBODIMENT (PHASE 17)")
    print("=" * 70)
    
    agent = EmbodiedAgent()
    
    # Initialize
    print("\n[Setup] Initializing embodied agent...")
    await agent.initialize_embodiment()
    print(f"  Sensors: {len(agent.sensory_processor.sensors)}")
    print(f"  Actuators: {len(agent.motor_controller.actuators)}")
    
    # Run interaction cycles
    print("\n[Interaction] Running sense-think-act cycles...")
    results = await agent.interaction_cycle(num_cycles=3)
    
    for result in results:
        print(f"  Cycle {result['cycle']}:")
        print(f"    Perceptions: {list(result['perception'].keys())}")
        print(f"    Intentions: {result['intentions']}")
        print(f"    Actions: {result['actions']}")
        print(f"    Success rate: {result['success_rate']:.1%}")
    
    # Attention weights
    print("\n[Attention] Sensory attention weights...")
    for sensor_type, weight in agent.sensory_processor.attention_weights.items():
        print(f"  {sensor_type.value}: {weight:.2f}")
    
    # Final state
    print("\n[State] Embodiment state...")
    state = await agent.get_embodiment_state()
    print(f"  Total sensors: {state['sensors_registered']}")
    print(f"  Total actuators: {state['actuators_registered']}")
    print(f"  Sensory readings: {state['sensory_readings']}")
    print(f"  Motor commands: {state['motor_commands']['commands_executed']}")
    print(f"  Motor success rate: {state['motor_commands']['success_rate']:.1%}")
    print(f"  Interaction cycles: {state['interaction_cycles']}")
    print(f"  Total actions: {state['total_actions']}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(demo_embodied_agent())
