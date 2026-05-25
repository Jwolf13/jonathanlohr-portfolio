

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime


from app.db.base import Base

class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) # ISO format timestamp

 


class Metric(TimestampMixin,Base):
    """A measurable athletic test (e.g., 40-Yard Dash, Vertical Jump)."""

    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))   # e.g. "40-Yard Dash"
    unit: Mapped[str] = mapped_column(String(50))                  # e.g. "seconds", "inches"
    category: Mapped[str] = mapped_column(String(50))              # e.g. "speed", "strength"
    description: Mapped[str | None] = mapped_column(String(500))

    
    protocols = relationship("Protocol", back_populates="metric", cascade="all, delete-orphan",passive_deletes=True)
    benchmarks = relationship("Benchmark", back_populates="metric", cascade="all, delete-orphan", passive_deletes=True)
 


class Benchmark(TimestampMixin, Base):
    """An elite performance standard tied to a specific Metric."""

    __tablename__ = "benchmarks"

    id: Mapped[int] = mapped_column(primary_key=True)
    metric_id: Mapped[int] = mapped_column(ForeignKey("metrics.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(50))    # e.g. "elite", "average", "below average"
    value: Mapped[float] = mapped_column(Float)        # the threshold value in Metric.unit
    gender: Mapped[str | None] = mapped_column(String(10))     # e.g. "male", "female", "any"
    age_group: Mapped[str | None] = mapped_column(String(20))  # e.g. "18-24", "open"

  
    metric = relationship("Metric", back_populates="benchmarks")
    



class Protocol(TimestampMixin, Base):
    """A workout protocol that can be scaled to an athlete's evaluation results."""

    __tablename__ = "protocols"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50))   # e.g. "strength", "conditioning"
    description: Mapped[str | None] = mapped_column(String(500))
    sets: Mapped[int | None] = mapped_column(Integer)
    reps: Mapped[int | None] = mapped_column(Integer)
    rest_seconds: Mapped[int | None] = mapped_column(Integer)
    load_unit: Mapped[str | None] = mapped_column(String(50))  
    metric_id: Mapped[int] = mapped_column(ForeignKey("metrics.id", ondelete="CASCADE"), index=True) 
    scaling_factor: Mapped[float] = mapped_column(Float, default=1.0)  # e.g. 0.8 means 80% of the elite benchmark
    metric = relationship("Metric", back_populates="protocols")


    
