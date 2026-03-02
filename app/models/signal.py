import uuid
from datetime import datetime

from sqlalchemy import (
    String, Integer, Float, Text, DateTime, ForeignKey, func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    audit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("audits.id"), nullable=False, index=True
    )
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=False, index=True
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    signal_text: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    score_type: Mapped[str] = mapped_column(String(10), nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=False)
    failure_scenario: Mapped[str] = mapped_column(Text, nullable=False)
    remediation: Mapped[str] = mapped_column(Text, nullable=False)
    effort: Mapped[str] = mapped_column(String(5), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    references: Mapped[list] = mapped_column(JSONB, default=list)
    phase_number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    audit = relationship("Audit", back_populates="signals")
    category = relationship("Category", lazy="joined")
