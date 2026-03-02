import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RepoSnapshot(Base):
    __tablename__ = "repo_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    audit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("audits.id"), unique=True, nullable=False
    )
    repo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    commit_sha: Mapped[str | None] = mapped_column(String(40), nullable=True)
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    file_index: Mapped[dict] = mapped_column(JSONB, default=dict)
    git_analysis: Mapped[dict] = mapped_column(JSONB, default=dict)
    local_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cloned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    audit = relationship("Audit", back_populates="repo_snapshot")
    artifacts = relationship("Artifact", back_populates="snapshot", lazy="noload")


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repo_snapshots.id"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    snapshot = relationship("RepoSnapshot", back_populates="artifacts")
