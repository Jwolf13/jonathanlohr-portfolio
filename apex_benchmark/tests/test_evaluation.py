import pytest
from app.services.evaluation import evaluate_output_metric, evaluate_timed_metric


class TestEvaluateOutputMetric:

    def test_normal_case(self):
        result = evaluate_output_metric(28.0, 36.0)
        assert result == pytest.approx(0.777, rel=1e-2) #means within 1% tolerance
    
    def test_exceeds_elite(self):
        result = evaluate_output_metric(40.0, 36.0)
        assert result > 1.0   # what operator? your function returns the raw ratio

    def test_exactly_elite(self):
        result = evaluate_output_metric(30.0, 30.0)
        assert result == 1.0

    def test_zero_score_returns_zero(self):
        with pytest.raises(ValueError):
            evaluate_output_metric(0.0, 30.0)

    def test_zero_baseline_raises(self):
        with pytest.raises(ValueError):
            evaluate_output_metric(30.0, 0.0)

    def test_negative_score_raises(self):
        with pytest.raises(ValueError):
            evaluate_output_metric(-5.0, 30.0)


class TestEvaluateTimedMetric:

    def test_normal_case(self):
        result = evaluate_timed_metric(4.6, 4.3)
        assert result == pytest.approx(0.935, rel=1e-2) #means within 1% tolerance

    def test_exactly_elite(self):
        result = evaluate_timed_metric(4.3, 4.3)
        assert result == 1.0

    def test_faster_than_elite(self):
        result = evaluate_timed_metric(4.0, 4.3)
        assert result == pytest.approx(1.075, rel=1e-2) #means within 1% tolerance

    def test_zero_time_raises(self):
        with pytest.raises(ValueError):
            evaluate_timed_metric(0.0, 4.3)

    def test_zero_baseline_raises(self):
        with pytest.raises(ValueError):
            evaluate_timed_metric(4.6, 0.0)

    def test_negative_time_raises(self):
        with pytest.raises(ValueError):
            evaluate_timed_metric(-5.0, 4.3)