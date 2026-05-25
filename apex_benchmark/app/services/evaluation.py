def evaluate_timed_metric(user_score: float, elite_baseline: float) -> float:
    """
    Score a timed metric where a lower result is better (e.g., 40-Yard Dash).

    A user who matches the elite_baseline should receive a perfect score.
    A user who is slower than the baseline should receive a proportionally
    lower score. The return value is a normalised float representing
    performance relative to the elite standard.
    """
    if elite_baseline <= 0:
        raise ValueError("Elite baseline must be greater than zero.")
    if user_score <= 0:
        raise ValueError("User score must be non-negative.")
    ratio = elite_baseline / user_score
    return ratio




def evaluate_output_metric(user_score: float, elite_baseline: float) -> float:
    """
    Score an output metric where a higher result is better
    (e.g., Vertical Jump, Back Squat, VO2 Max).

    A user who matches the elite_baseline should receive a perfect score.
    A user who falls short of the baseline should receive a proportionally
    lower score. The return value is a normalised float representing
    performance relative to the elite standard.
    """

    if elite_baseline <= 0:
        raise ValueError("Elite baseline must be greater than zero.")
    if user_score <= 0:
        raise ValueError("User score must be greater than zero.")
    if user_score == elite_baseline:
        return 1.0  # Perfect score if the user matches the elite baseline
    ratio = user_score / elite_baseline
    return ratio

def determine_tier(
    user_value: float,
    elite: float,
    average: float,
    below_average: float,
    category: str,
  ) -> str:
    if category == "speed":
        if user_value <= elite:
            return "elite"
        elif user_value <= average:
            return "average"
        else:
            return "below average"
    else:
        if user_value >= elite:
            return "elite"
        elif user_value >= average:
            return "average"
        else:
            return "below average"
