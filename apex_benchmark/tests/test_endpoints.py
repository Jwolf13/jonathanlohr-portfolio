from fastapi.testclient import TestClient
import pytest
from app.main import main



client = TestClient(main)

def test_list_metrics():
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    assert isinstance(response.json(), list)  # Should return a list of metrics

def test_evaluate_user():
    response = client.post("/api/v1/evaluate", json={
        "metric_id": 9,
        "user_value": 4.6, # Example user input for 40-Yard Dash
        "gender": "male",
        "age": 24,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["performance_tier"] == "average"
    assert data ["score"] == pytest.approx(0.935, 0.001)

def test_evaluate_user_metric_not_found():
    response = client.post("/api/v1/evaluate", json={
        "metric_id": 9999,
        "user_value": 4.6,
        "gender": "male",
        "age": 24,
    })
    assert response.status_code == 404
    assert response.json()["detail"] == "Metric not found." 

def test_evaluate_user_missing_field():
    response = client.post("/api/v1/evaluate", json={
        "metric_id": 9,
        "gender": "male",
        "age": 24,
    })
    assert response.status_code == 422
