"""
PHASE 8 QUANTUM INTEGRATION — TEST SUITE
Test quantum engine, QAOA, VQE, and quantum-inspired algorithms
"""

import pytest
import asyncio
from typing import Dict, Any

from pradysagican.quantum.quantum_engine import (
    QuantumEngine,
    QuantumCircuit,
    QAOAOptimizer,
    VariationalQuantumEigensolver,
    QuantumInspiredOptimizer,
    GateType,
    initialize_quantum_engine
)


class TestQuantumCircuit:
    """Test quantum circuit functionality."""
    
    def test_circuit_creation(self):
        """Test creating a quantum circuit."""
        circuit = QuantumCircuit(3, "test")
        assert circuit.num_qubits == 3
        assert circuit.name == "test"
        assert len(circuit.gates) == 0
    
    def test_add_hadamard_gate(self):
        """Test adding Hadamard gate."""
        circuit = QuantumCircuit(2)
        circuit.h(0)
        assert len(circuit.gates) == 1
        assert circuit.gates[0].gate_type == GateType.HADAMARD
    
    def test_add_cnot_gate(self):
        """Test adding CNOT gate."""
        circuit = QuantumCircuit(2)
        circuit.cnot(0, 1)
        assert len(circuit.gates) == 1
        assert circuit.gates[0].gate_type == GateType.CNOT
        assert circuit.gates[0].control_qubits == [0]
    
    def test_circuit_depth(self):
        """Test circuit depth calculation."""
        circuit = QuantumCircuit(3)
        circuit.h(0)
        circuit.cnot(0, 1)
        circuit.h(2)
        assert circuit.get_depth() == 3
    
    def test_gate_count(self):
        """Test gate counting."""
        circuit = QuantumCircuit(3)
        circuit.h(0)
        circuit.h(1)
        circuit.x(2)
        counts = circuit.get_gate_count()
        assert counts["h"] == 2
        assert counts["x"] == 1


class TestQuantumEngine:
    """Test quantum engine."""
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self):
        """Test quantum engine initialization."""
        engine = await initialize_quantum_engine()
        assert engine is not None
        assert engine.max_qubits == 20
    
    def test_create_circuit(self):
        """Test creating circuits."""
        engine = QuantumEngine()
        circuit = engine.create_circuit(4, "demo")
        assert circuit.num_qubits == 4
        assert "demo" in engine.circuits
    
    def test_qubit_limit(self):
        """Test qubit limit enforcement."""
        engine = QuantumEngine(max_qubits=10)
        with pytest.raises(ValueError):
            engine.create_circuit(15)
    
    @pytest.mark.asyncio
    async def test_simulate_circuit(self):
        """Test circuit simulation."""
        engine = QuantumEngine()
        circuit = engine.create_circuit(2, "sim_test")
        circuit.h(0)
        circuit.cnot(0, 1)
        circuit.measure()
        
        result = await engine.simulate_circuit(circuit)
        assert result.most_likely is not None
        assert result.measurement_quality > 0
        assert len(result.counts) > 0


class TestQAOA:
    """Test QAOA optimizer."""
    
    @pytest.mark.asyncio
    async def test_qaoa_initialization(self):
        """Test QAOA optimizer creation."""
        qaoa = QAOAOptimizer(problem_size=5, layers=2)
        assert qaoa.problem_size == 5
        assert qaoa.layers == 2
    
    @pytest.mark.asyncio
    async def test_qaoa_optimization(self):
        """Test QAOA optimization."""
        qaoa = QAOAOptimizer(3, 1)
        
        async def simple_cost(gamma, beta):
            return (gamma - 0.7)**2 + (beta - 0.5)**2
        
        result = await qaoa.optimize(simple_cost, iterations=10)
        assert "best_cost" in result
        assert "best_params" in result
        assert result["converged"]


class TestVQE:
    """Test Variational Quantum Eigensolver."""
    
    @pytest.mark.asyncio
    async def test_vqe_initialization(self):
        """Test VQE initialization."""
        vqe = VariationalQuantumEigensolver(3)
        assert vqe.num_qubits == 3
    
    @pytest.mark.asyncio
    async def test_find_ground_state(self):
        """Test ground state finding."""
        vqe = VariationalQuantumEigensolver(2)
        hamiltonian = {(0,): -1.0, (1,): -1.0, (0, 1): 0.5}
        
        result = await vqe.find_ground_state(hamiltonian, iterations=5)
        assert "ground_state_energy" in result
        assert "energy_history" in result
        assert result["converged"]


class TestQuantumInspired:
    """Test quantum-inspired classical algorithms."""
    
    @pytest.mark.asyncio
    async def test_grover_inspired(self):
        """Test Grover-inspired search."""
        result = await QuantumInspiredOptimizer.grover_inspired_search(100)
        assert result["search_space"] == 100
        assert result["quantum_iterations"] > 0
        assert result["speedup_factor"] > 0
    
    @pytest.mark.asyncio
    async def test_speedup_calculation(self):
        """Test speedup calculations."""
        # Large search space should show speedup
        result = await QuantumInspiredOptimizer.grover_inspired_search(10000)
        assert result["speedup_factor"] > 10


class TestQuantumIntegration:
    """Integration tests for quantum system."""
    
    @pytest.mark.asyncio
    async def test_quantum_workflow(self):
        """Test complete quantum workflow."""
        # Create engine
        engine = QuantumEngine(max_qubits=10)
        
        # Create circuit
        circuit = engine.create_circuit(3, "workflow")
        circuit.h(0)
        circuit.cnot(0, 1)
        circuit.cnot(1, 2)
        circuit.measure()
        
        # Simulate
        result = await engine.simulate_circuit(circuit)
        
        assert result.most_likely is not None
        assert result.measurement_quality > 0.8
    
    @pytest.mark.asyncio
    async def test_qaoa_workflow(self):
        """Test QAOA workflow."""
        qaoa = QAOAOptimizer(4, 1)
        
        async def cost_func(g, b):
            return g * b
        
        result = await qaoa.optimize(cost_func, iterations=5)
        assert result["best_cost"] is not None


# Run tests: pytest tests/test_quantum_phase_8.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
