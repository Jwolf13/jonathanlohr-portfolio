"""
Entrypoint script for seeding the ApexBench database with elite benchmark data.

Run from the project root with the venv active:
    python -m app.db.seed
"""

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.athletic import Benchmark, Metric, Protocol


def seed_database(db: Session) -> None:
    """Insert base Metric rows and their elite Benchmark standards."""

    # ── 40-Yard Dash ─────────────────────────────────────────────────────────
    metric_40 = Metric(
        name="40-Yard Dash",
        unit="seconds",
        category="speed",
        description="A sprint covering 40 yards, commonly used to assess acceleration and top-end speed.",
    )
    db.add(metric_40)
    db.flush()  # flush to assign an ID to the metric for the ForeignKey 

    db.add(Benchmark(metric_id=metric_40.id, label="elite", value=4.3, gender="male"))
    db.add(Benchmark(metric_id=metric_40.id, label="average", value=4.6, gender="male"))
    db.add(Benchmark(metric_id=metric_40.id, label="below average", value=4.9, gender="male"))
    db.add(Benchmark(metric_id=metric_40.id, label="elite", value=4.6, gender="female"))
    db.add(Benchmark(metric_id=metric_40.id, label="average", value=4.9, gender="female"))
    db.add(Benchmark(metric_id=metric_40.id, label="below average", value=5.2, gender="female"))



    protocol = Protocol(
        name= "Sprint Acceleration Block",
        category="speed",
        description=" speed workout protocol scaled to 40-Yard Dash performance.",
        sets=3,
        reps=5,
        rest_seconds=30,
        load_unit="N/A",
        scaling_factor=1.0,  # This could be used to adjust the workout intensity based on the evaluation score
        metric_id = metric_40.id
    )
    db.add(protocol)
 
    # TODO: create a Metric row → name="40-Yard Dash", unit="seconds",
    #       category="speed"
    # TODO: create Benchmark rows for this metric:
    #         label="elite",         value=<elite time>,    gender="male"
    #         label="average",       value=<average time>,  gender="male"
    #         label="below average", value=<below time>,    gender="male"
    #       (repeat set for gender="female" with appropriate values)
    # TODO: db.add() each object and flush so the metric.id is available
    #       for the ForeignKey on each Benchmark row

    # ── Vertical Jump ─────────────────────────────────────────────────────────
    metric_vertical_jump = Metric(
        name="Vertical Jump",
        unit="inches",
        category="power",
        description="A test of lower-body explosive power, measuring the maximum height an athlete can jump from a standstill.",
    )
    db.add(metric_vertical_jump)
    db.flush()  # flush to assign an ID to the metric for the ForeignKey    

    db.add(Benchmark(metric_id=metric_vertical_jump.id, label="elite", value=36.0, gender="male"))
    db.add(Benchmark(metric_id=metric_vertical_jump.id, label="average", value=30.0, gender="male"))
    db.add(Benchmark(metric_id=metric_vertical_jump.id, label="below average", value=28.0, gender="male"))
    db.add(Benchmark(metric_id=metric_vertical_jump.id, label="elite", value=28.0, gender="female"))
    db.add(Benchmark(metric_id=metric_vertical_jump.id, label="average", value=24.0, gender="female"))
    db.add(Benchmark(metric_id=metric_vertical_jump.id, label="below average", value=20.0, gender="female"))


    protocol = Protocol(
        name= "Plyometric Power Series",
        category="power",
        description=" power workout protocol scaled to Vertical Jump performance.",
        sets=4,
        reps=8,
        rest_seconds=60,
        load_unit="N/A",
        scaling_factor=1.0,  # This could be used to adjust the workout intensity based on the evaluation score
        metric_id = metric_vertical_jump.id
    )
    db.add(protocol)    

    # TODO: create a Metric row → name="Vertical Jump", unit="inches",
    #       category="power"
    # TODO: create Benchmark rows for this metric:
    #         label="elite",         value=<elite inches>,   gender="male"
    #         label="average",       value=<average inches>, gender="male"
    #         label="below average", value=<below inches>,   gender="male"
    #       (repeat for gender="female")
    # TODO: db.add() each object

    # ── Back Squat ────────────────────────────────────────────────────────────
    metric_back_squat = Metric(
        name="Back Squat",
        unit="bodyweight multiplier",
        category="strength",
        description="A compound strength exercise where the athlete squats with a barbell across their upper back.",
    )
    db.add(metric_back_squat)
    db.flush()  # flush to assign an ID to the metric for the ForeignKey        

    db.add(Benchmark(metric_id=metric_back_squat.id, label="elite", value=2.0, gender="male"))
    db.add(Benchmark(metric_id=metric_back_squat.id, label="average", value=1.5, gender="male"))            
    db.add(Benchmark(metric_id=metric_back_squat.id, label="below average", value=1.0, gender="male"))
    db.add(Benchmark(metric_id=metric_back_squat.id, label="elite", value=1.5, gender="female"))
    db.add(Benchmark(metric_id=metric_back_squat.id, label="average", value=1.0, gender="female"))
    db.add(Benchmark(metric_id=metric_back_squat.id, label="below average", value=0.5, gender="female"))


    protocol = Protocol(
        name= "Strength Progression Block",
        category="strength",
        description="A sample strength workout protocol scaled to Back Squat performance.",
        sets=5,
        reps=5,
        rest_seconds=120,
        load_unit="x bodyweight",
        scaling_factor=1.0,  # This could be used to adjust the workout intensity based on the evaluation score
        metric_id = metric_back_squat.id
    )
    db.add(protocol)    
    # TODO: create a Metric row → name="Back Squat", unit="lbs",
    #       category="strength"
    # NOTE: Back Squat elite standards are typically expressed as a
    #       bodyweight multiplier — decide whether to store the raw lb value
    #       or a multiplier and adjust the column type accordingly.
    # TODO: create Benchmark rows (label, value, gender, age_group)
    # TODO: db.add() each object

    # ── VO2 Max ───────────────────────────────────────────────────────────────
    metric_vo2_max = Metric(
        name="VO2 Max",
        unit="ml/kg/min",
        category="endurance",
        description="The maximum rate of oxygen consumption measured during incremental exercise.",
    )
    db.add(metric_vo2_max)
    db.flush()  # flush to assign an ID to the metric for the ForeignKey    

    db.add(Benchmark(metric_id=metric_vo2_max.id, label="elite", value=60.0, gender="male"))
    db.add(Benchmark(metric_id=metric_vo2_max.id, label="average", value=45.0, gender="male"))
    db.add(Benchmark(metric_id=metric_vo2_max.id, label="below average", value=30.0, gender="male"))
    db.add(Benchmark(metric_id=metric_vo2_max.id, label="elite", value=60.0, gender="female"))
    db.add(Benchmark(metric_id=metric_vo2_max.id, label="average", value=45.0, gender="female"))
    db.add(Benchmark(metric_id=metric_vo2_max.id, label="below average", value=30.0, gender="female"))

    
    protocol = Protocol(
        name= "Aerobic Base Builder",
        category="endurance",
        description="A sample endurance workout protocol scaled to VO2 Max performance.",
        sets=3,
        reps=10,        
        rest_seconds=90,    
        load_unit="N/A",
        scaling_factor=1.0,  # This could be used to adjust the workout intensity based on the evaluation score
        metric_id = metric_vo2_max.id
    )
    db.add(protocol)    



    # TODO: create a Metric row → name="VO2 Max", unit="ml/kg/min",
    #       category="endurance"
    # NOTE: VO2 Max norms vary significantly by age and gender — consider
    #       populating multiple age_group rows (e.g. "18-24", "25-34", etc.)
    # TODO: create Benchmark rows with age_group set appropriately
    # TODO: db.add() each object

    # ── Protocol seeds (optional first pass) ─────────────────────────────────
     
    # TODO: insert base Protocol rows for any starter workouts you want
    #       available before user-generated content is added

    # ── Commit ────────────────────────────────────────────────────────────────
    db.commit()  # commit all the above changes to the database

    # TODO: db.commit() once all objects have been added


if __name__ == "__main__":
    db: Session = SessionLocal()
    try:
        seed_database(db)
        print("Seed complete.")
    except Exception as exc:
        db.rollback()
        print(f"Seed failed: {exc}")
        raise
    finally:
        db.close()
