"""The schema, straight out of the ER diagram (zenai-lucidchart-diagrams.md #3).

Frozen in M0 -- every agent builds against these.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True)
    # Never a real name. ZenAI holds a pseudonym and nothing identifying.
    pseudonym: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Consent(Base):
    __tablename__ = "consents"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    scope: Mapped[str] = mapped_column(String(64))  # remember_mood|remember_topics|...
    granted: Mapped[bool] = mapped_column(Boolean, default=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Turn(Base):
    __tablename__ = "turns"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    # Post-Privacy-Agent. The raw text is never persisted.
    student_text_redacted: Mapped[str] = mapped_column(Text)
    reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    regeneration_count: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MoodPoint(Base):
    __tablename__ = "mood_points"
    id: Mapped[int] = mapped_column(primary_key=True)
    turn_id: Mapped[int] = mapped_column(ForeignKey("turns.id"))
    primary_emotion: Mapped[str] = mapped_column(String(32))
    distress_score: Mapped[float] = mapped_column(Float)
    full_distribution: Mapped[dict] = mapped_column(JSON, default=dict)


class FidelityScore(Base):
    """One row per generated reply, scored against the six ACT processes.

    This table IS the contribution -- experiments E1 and E3 are queries over it.
    """

    __tablename__ = "fidelity_scores"
    id: Mapped[int] = mapped_column(primary_key=True)
    turn_id: Mapped[int] = mapped_column(ForeignKey("turns.id"))
    acceptance: Mapped[float] = mapped_column(Float, default=0.0)
    defusion: Mapped[float] = mapped_column(Float, default=0.0)
    present_moment: Mapped[float] = mapped_column(Float, default=0.0)
    self_as_context: Mapped[float] = mapped_column(Float, default=0.0)
    values: Mapped[float] = mapped_column(Float, default=0.0)
    committed_action: Mapped[float] = mapped_column(Float, default=0.0)
    passed: Mapped[bool] = mapped_column(Boolean, default=True)
    # advice_giving | diagnosis | false_reassurance | none
    drift_type: Mapped[str] = mapped_column(String(32), default="none")
    monitor_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class Escalation(Base):
    __tablename__ = "escalations"
    id: Mapped[int] = mapped_column(primary_key=True)
    turn_id: Mapped[int] = mapped_column(ForeignKey("turns.id"))
    risk_score: Mapped[float] = mapped_column(Float)
    action_taken: Mapped[str] = mapped_column(String(64))
    at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MemoryItem(Base):
    __tablename__ = "memory_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    content: Mapped[str] = mapped_column(Text)
    scope: Mapped[str] = mapped_column(String(64))
    # The student can delete anything ZenAI remembers. Non-negotiable.
    student_deletable: Mapped[bool] = mapped_column(Boolean, default=True)


class ProgressSnapshot(Base):
    __tablename__ = "progress_snapshots"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    week: Mapped[date] = mapped_column(Date)
    avg_distress: Mapped[float] = mapped_column(Float)
    themes: Mapped[dict] = mapped_column(JSON, default=dict)
