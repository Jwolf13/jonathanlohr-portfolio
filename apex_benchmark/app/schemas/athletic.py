from pydantic import BaseModel


class MetricResponse(BaseModel):
    """Serializes a Metric row for API responses."""

    id: int
    name: str
    unit: str
    category: str
    description: str | None

    # TODO: add validator to normalise category to lowercase if needed
    # TODO: add nested BenchmarkResponse list once that schema exists

    model_config = {"from_attributes": True}


class UserEvaluationRequest(BaseModel):
    """Incoming payload when a user submits their test result for evaluation."""

    metric_id: int
    user_value: float           # the raw result in the metric's unit
    gender: str                 # "male" | "female"
    age: int                    # used to select the correct benchmark age_group

    # TODO: add @field_validator for gender to enforce allowed values
    # TODO: add @field_validator for age to enforce a reasonable range (e.g. 13–99)
    # TODO: add @model_validator to cross-check metric_id exists before scoring


class WorkoutResponse(BaseModel):
    """Serializes a Protocol row as a prescribed workout for API responses."""

    id: int
    name: str
    category: str
    description: str | None
    sets: int | None
    reps: int | None
    rest_seconds: int | None
    load_unit: str | None
    performance_tier: str  # e.g. "elite", "average", "below average"
    score: float           # the normalised score from the evaluation (0.0 to 1.0)
    

    # TODO: add scaled_load field once the scaling calculation logic is implemented
    # TODO: add validator to format rest_seconds as "mm:ss" string for display

    model_config = {"from_attributes": True}
