from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.athletic import MetricResponse, UserEvaluationRequest, WorkoutResponse
from app.models.athletic import Benchmark, Metric, Protocol
from app.services.evaluation import evaluate_output_metric, evaluate_timed_metric, determine_tier


router = APIRouter()


@router.get(
    "/metrics",
    response_model=list[MetricResponse],
    summary="List all athletic metrics",
)
def list_metrics(db: Session = Depends(get_db)) -> list[MetricResponse]:
    """Return the full directory of measurable athletic tests."""
    
    metrics = db.query(Metric).all()
    return metrics



@router.post(
    "/evaluate",
    response_model=WorkoutResponse,
    summary="Evaluate a user's test result and return a scaled workout",
)
def evaluate_user(
    payload: UserEvaluationRequest,
    db: Session = Depends(get_db),
) -> WorkoutResponse:
    """
    Accept a user's raw score for a given metric, compare it against
    the elite benchmark, and return a scaled Protocol as a WorkoutResponse.
    """
    metric = db.query(Metric).filter(Metric.id == payload.metric_id).first()
    if metric is None:
        raise HTTPException(status_code=404, detail="Metric not found.")



    benchmarks = db.query(Benchmark).filter(
        Benchmark.metric_id == metric.id,
        Benchmark.gender == payload.gender,
      ).all()

    elite_benchmark = next((b for b in benchmarks if b.label == "elite"), None)
    average_benchmark = next((b for b in benchmarks if b.label == "average"), None)
    below_average_benchmark = next((b for b in benchmarks if b.label == "below average"), None)

    if elite_benchmark is None:
        raise HTTPException(status_code=404, detail="Elite benchmark not found.")
    if average_benchmark is None:
        raise HTTPException(status_code=404, detail="Average benchmark not found.")
    if below_average_benchmark is None:
        raise HTTPException(status_code=404, detail="Below average benchmark not found.")
    

    protocol = db.query(Protocol).filter(Protocol.metric_id == metric.id).first()
    if protocol is None:
        raise HTTPException(status_code=404, detail="Protocol not found.")  
    
    if metric.category == "speed":
        score = evaluate_timed_metric(payload.user_value, elite_benchmark.value)
    else:
        score = evaluate_output_metric(payload.user_value, elite_benchmark.value)

    tier = determine_tier(
          payload.user_value,
          elite_benchmark.value,
          average_benchmark.value,
          below_average_benchmark.value,
          metric.category,
      )
    return WorkoutResponse(
        id=protocol.id,
        name=protocol.name,
        category=protocol.category,
        description=protocol.description,
        sets=protocol.sets,
        reps=protocol.reps,
        rest_seconds=protocol.rest_seconds,
        load_unit=protocol.load_unit,
        performance_tier= tier,
        score=round(score, 3),
      )
