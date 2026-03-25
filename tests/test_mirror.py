"""
Tests for MIRROR metacognitive calibration system (F271–F280).

Test coverage:
- Confidence calibration tracking
- Calibration curves
- Blindsight detection
- Stability monitoring
- Vital signs
"""

import pytest
import statistics

from pradysagican.core.mirror import (
    Mirror,
    CalibrationEngine,
    CalibrationCurve,
    StabilityModel,
    VitalSignsMonitor,
    ConfidenceEstimate,
    CalibrationMetrics,
    get_mirror,
)


class TestCalibrationCurve:
    """Test calibration curve creation and analysis."""
    
    def test_curve_creation(self):
        """Create calibration curve."""
        curve = CalibrationCurve("test_tool", bins=10)
        assert curve.tool_name == "test_tool"
        assert curve.bins == 10
    
    def test_add_predictions(self):
        """Add predictions to curve."""
        curve = CalibrationCurve("test_tool")
        curve.add_prediction(0.8, 0.9)
        curve.add_prediction(0.7, 0.6)
        
        data = curve.get_calibration_data()
        assert len(data) >= 1
    
    def test_perfect_calibration(self):
        """Perfect calibration: confidence == accuracy."""
        curve = CalibrationCurve("test_tool")
        
        # Add perfectly calibrated predictions
        for i in range(10):
            curve.add_prediction(0.5, 0.5)
        
        error = curve.get_calibration_error()
        assert error < 0.01  # Nearly zero error


class TestCalibrationEngine:
    """Test calibration engine."""
    
    def test_engine_creation(self):
        """Create calibration engine."""
        engine = CalibrationEngine()
        assert len(engine.estimates) == 0
        assert len(engine.curves) == 0
    
    def test_record_estimate(self):
        """Record confidence estimate."""
        engine = CalibrationEngine()
        engine.record_estimate("tool", "task_1", 0.85)
        
        assert len(engine.estimates) == 1
        assert "tool" in engine.curves
    
    def test_record_ground_truth(self):
        """Record ground truth accuracy."""
        engine = CalibrationEngine()
        engine.record_estimate("tool", "task_1", 0.85)
        engine.record_ground_truth("tool", "task_1", 0.90)
        
        # Find the estimate
        matching = [e for e in engine.estimates if e.task_id == "task_1"]
        assert len(matching) == 1
        assert matching[0].actual_accuracy == 0.90
    
    def test_metrics_calculation(self):
        """Metrics are calculated from predictions."""
        engine = CalibrationEngine()
        
        # Record several predictions
        for i in range(10):
            engine.record_estimate("tool", f"task_{i}", 0.8)
            engine.record_ground_truth("tool", f"task_{i}", 0.9 if i < 8 else 0.1)
        
        metrics = engine.get_metrics("tool")
        assert metrics is not None
        assert metrics.total_predictions == 10
    
    def test_detect_overconfidence(self):
        """Detect overconfident tool."""
        engine = CalibrationEngine()
        
        # High confidence, low accuracy
        for i in range(10):
            engine.record_estimate("tool", f"task_{i}", 0.95)
            engine.record_ground_truth("tool", f"task_{i}", 0.30)
        
        overconfident = engine.detect_overconfidence(threshold=0.5)
        assert "tool" in overconfident
    
    def test_detect_blindsights(self):
        """Detect blindsight areas."""
        engine = CalibrationEngine()
        
        # High confidence, low accuracy
        for i in range(10):
            engine.record_estimate("tool", f"task_{i}", 0.9)
            engine.record_ground_truth("tool", f"task_{i}", 0.2)
        
        blindsights = engine.detect_blindsights()
        assert len(blindsights) >= 1


class TestStabilityModel:
    """Test stability monitoring."""
    
    def test_model_creation(self):
        """Create stability model."""
        model = StabilityModel()
        assert len(model.accuracy_history) == 0
    
    def test_record_accuracy(self):
        """Record accuracy measurements."""
        model = StabilityModel()
        model.record_accuracy("tool", 0.85)
        model.record_accuracy("tool", 0.87)
        
        assert len(model.accuracy_history["tool"]) == 2
    
    def test_detect_improvement_trend(self):
        """Detect improving accuracy trend."""
        model = StabilityModel()
        
        # Record improving trend
        for i in range(20):
            model.record_accuracy("tool", 0.5 + i * 0.02)
        
        trend = model.get_trend("tool")
        assert trend == "improving"
    
    def test_detect_declining_trend(self):
        """Detect declining accuracy trend."""
        model = StabilityModel()
        
        # Record declining trend
        for i in range(20):
            model.record_accuracy("tool", 0.9 - i * 0.02)
        
        trend = model.get_trend("tool")
        assert trend == "declining"
    
    def test_detect_drift(self):
        """Detect accuracy drift."""
        model = StabilityModel(window_size=20)
        
        # Record stable first half, then drift down second half
        for i in range(10):
            model.record_accuracy("tool", 0.9)
        for i in range(10):
            model.record_accuracy("tool", 0.6)
        
        drift_detected = model.detect_drift("tool", threshold=0.2)
        assert drift_detected


class TestVitalSignsMonitor:
    """Test vital signs monitoring."""
    
    def test_monitor_creation(self):
        """Create vital signs monitor."""
        monitor = VitalSignsMonitor()
        assert len(monitor.vital_signs) == 0
    
    def test_set_vital_sign_ok(self):
        """Set vital sign with ok severity."""
        monitor = VitalSignsMonitor()
        monitor.set_vital_sign("latency_ms", 50, (40, 100))
        
        signs = monitor.get_vital_signs()
        assert "latency_ms" in signs
        assert signs["latency_ms"].severity == "ok"
    
    def test_set_vital_sign_warning(self):
        """Set vital sign with warning severity."""
        monitor = VitalSignsMonitor()
        monitor.set_vital_sign("latency_ms", 20, (40, 100))  # Below normal
        
        signs = monitor.get_vital_signs()
        assert signs["latency_ms"].severity == "warning"
    
    def test_set_vital_sign_critical(self):
        """Set vital sign with critical severity."""
        monitor = VitalSignsMonitor()
        monitor.set_vital_sign("latency_ms", 1000, (40, 100))  # Far above normal
        
        signs = monitor.get_vital_signs()
        assert signs["latency_ms"].severity == "critical"
    
    def test_health_status(self):
        """Compute overall health status."""
        monitor = VitalSignsMonitor()
        monitor.set_vital_sign("latency", 50, (40, 100))
        monitor.set_vital_sign("memory", 500, (400, 1000))
        
        status = monitor.health_status()
        assert status == "healthy"


class TestMirror:
    """Test main MIRROR system."""
    
    def test_mirror_creation(self):
        """Create MIRROR instance."""
        mirror = Mirror()
        assert mirror.calibration is not None
        assert mirror.stability is not None
        assert mirror.vital_signs is not None
    
    def test_record_estimate_and_truth(self):
        """Record both estimate and ground truth."""
        mirror = Mirror()
        mirror.record_estimate_and_truth("tool", "task_1", 0.85, 0.90)
        
        metrics = mirror.calibration.get_metrics("tool")
        assert metrics is not None
        assert metrics.total_predictions == 1
    
    def test_calibration_report(self):
        """Generate calibration report."""
        mirror = Mirror()
        
        # Record some data
        for i in range(5):
            mirror.record_estimate_and_truth("tool", f"task_{i}", 0.8, 0.85)
        
        report = mirror.get_calibration_report()
        assert "total_tools" in report
        assert "metrics" in report
        assert "tool" in report["metrics"]
    
    def test_health_report(self):
        """Generate health report."""
        mirror = Mirror()
        mirror.vital_signs.set_vital_sign("latency_ms", 50, (40, 100))
        
        report = mirror.get_health_report()
        assert "vital_signs" in report
        assert "health_status" in report
    
    def test_full_report(self):
        """Generate comprehensive report."""
        mirror = Mirror()
        
        # Add some data
        for i in range(3):
            mirror.record_estimate_and_truth("tool", f"task_{i}", 0.8, 0.85)
        mirror.vital_signs.set_vital_sign("latency_ms", 50, (40, 100))
        
        report = mirror.get_full_report()
        assert "calibration" in report
        assert "health" in report
        assert "timestamp" in report
    
    def test_global_mirror_instance(self):
        """Global MIRROR instance accessible."""
        mirror = get_mirror()
        assert mirror is not None
        assert isinstance(mirror, Mirror)


class TestConfidenceEstimate:
    """Test confidence estimate data class."""
    
    def test_create_estimate(self):
        """Create confidence estimate."""
        est = ConfidenceEstimate(
            tool_name="tool",
            task_id="task_1",
            estimated_confidence=0.85
        )
        
        assert est.tool_name == "tool"
        assert est.estimated_confidence == 0.85
        assert est.actual_accuracy is None


class TestIntegration:
    """Integration tests for MIRROR."""
    
    def test_full_calibration_workflow(self):
        """Full calibration workflow."""
        mirror = Mirror()
        
        # Simulate predictions from multiple tools
        for tool in ["summarizer", "classifier", "translator"]:
            for i in range(10):
                confidence = 0.7 + (i % 3) * 0.1
                accuracy = 0.6 + (i % 4) * 0.1
                mirror.record_estimate_and_truth(tool, f"task_{i}", confidence, accuracy)
        
        # Get reports
        cal_report = mirror.get_calibration_report()
        assert cal_report["total_tools"] >= 3
        
        # Check metrics for each tool
        for tool in ["summarizer", "classifier", "translator"]:
            metrics = mirror.calibration.get_metrics(tool)
            assert metrics.total_predictions == 10
