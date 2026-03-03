"""API endpoints for PE-grade report deliverables."""

import hashlib
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.audit import Audit
from app.models.signal import Signal
from app.models.tenant import Tenant
from app.reports.pe_report_template import PEReportGenerator

router = APIRouter()
_generator = PEReportGenerator()


async def _authenticate_by_key(
    key: str = Query(..., description="API key for authentication"),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    if not key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide ?key= query parameter.",
        )
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    result = await db.execute(
        select(Tenant).where(Tenant.api_key_hash == key_hash, Tenant.is_active.is_(True))
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )
    return tenant


async def _load_audit_signals(
    db: AsyncSession,
    audit_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> tuple[Audit, list[Signal]]:
    audit_result = await db.execute(
        select(Audit).where(Audit.id == audit_id, Audit.tenant_id == tenant_id)
    )
    audit = audit_result.scalar_one_or_none()
    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit not found or access denied.",
        )

    sig_result = await db.execute(
        select(Signal).where(Signal.audit_id == audit_id).order_by(Signal.sequence_number)
    )
    signals = list(sig_result.scalars().all())
    return audit, signals


def _audit_metadata(audit: Audit) -> dict:
    return {
        "audit_id": str(audit.id),
        "system_context": audit.system_context or {},
        "total_tokens": audit.total_tokens_used,
        "total_cost": audit.total_cost_usd,
    }


@router.get("/{audit_id}")
async def get_full_pe_report(
    audit_id: uuid.UUID,
    tenant: Tenant = Depends(_authenticate_by_key),
    db: AsyncSession = Depends(get_db),
):
    """Full PE-grade report with all deliverables."""
    audit_result = await db.execute(
        select(Audit).where(Audit.id == audit_id, Audit.tenant_id == tenant.id)
    )
    audit = audit_result.scalar_one_or_none()
    if not audit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found.")

    return await _generator.generate_full_pe_report(audit_id, db)


@router.get("/{audit_id}/executive-summary")
async def get_executive_summary(
    audit_id: uuid.UUID,
    tenant: Tenant = Depends(_authenticate_by_key),
    db: AsyncSession = Depends(get_db),
):
    """Executive summary with risk score, traffic light, and top findings."""
    audit, signals = await _load_audit_signals(db, audit_id, tenant.id)
    return _generator.generate_executive_summary(str(audit_id), signals, _audit_metadata(audit))


@router.get("/{audit_id}/heatmap")
async def get_risk_heatmap(
    audit_id: uuid.UUID,
    tenant: Tenant = Depends(_authenticate_by_key),
    db: AsyncSession = Depends(get_db),
):
    """40-category risk heatmap organized by audit phase."""
    audit, signals = await _load_audit_signals(db, audit_id, tenant.id)
    return _generator.generate_risk_heatmap(signals)


@router.get("/{audit_id}/spof-map")
async def get_spof_map(
    audit_id: uuid.UUID,
    tenant: Tenant = Depends(_authenticate_by_key),
    db: AsyncSession = Depends(get_db),
):
    """Single points of failure classified by type."""
    audit, signals = await _load_audit_signals(db, audit_id, tenant.id)
    return _generator.generate_spof_map(signals)


@router.get("/{audit_id}/compliance")
async def get_compliance_gap_matrix(
    audit_id: uuid.UUID,
    frameworks: str = Query("soc2,gdpr,hipaa", description="Comma-separated framework list"),
    tenant: Tenant = Depends(_authenticate_by_key),
    db: AsyncSession = Depends(get_db),
):
    """Compliance gap matrix with per-framework readiness scores."""
    audit, signals = await _load_audit_signals(db, audit_id, tenant.id)
    fw_list = [f.strip() for f in frameworks.split(",") if f.strip()]
    return _generator.generate_compliance_gap_matrix(signals, fw_list)


@router.get("/{audit_id}/tech-debt")
async def get_tech_debt_ledger(
    audit_id: uuid.UUID,
    tenant: Tenant = Depends(_authenticate_by_key),
    db: AsyncSession = Depends(get_db),
):
    """Tech debt ledger with cost estimates."""
    audit, signals = await _load_audit_signals(db, audit_id, tenant.id)
    return _generator.generate_tech_debt_ledger(signals)


@router.get("/{audit_id}/roadmap")
async def get_remediation_roadmap(
    audit_id: uuid.UUID,
    tenant: Tenant = Depends(_authenticate_by_key),
    db: AsyncSession = Depends(get_db),
):
    """Phased remediation roadmap with resource requirements."""
    audit, signals = await _load_audit_signals(db, audit_id, tenant.id)
    return _generator.generate_remediation_roadmap(signals)


@router.get("/{audit_id}/pdf")
async def download_pdf(
    audit_id: uuid.UUID,
    company: str = Query("Target Company", description="Company name for report cover"),
    tenant: Tenant = Depends(_authenticate_by_key),
    db: AsyncSession = Depends(get_db),
):
    """Download the full PE-grade report as a PDF."""
    audit, signals = await _load_audit_signals(db, audit_id, tenant.id)
    audit_meta = _audit_metadata(audit)

    compliance_reqs = (audit.system_context or {}).get("compliance_requirements", [])
    frameworks = compliance_reqs if compliance_reqs else ["soc2", "gdpr", "hipaa"]

    report_data = _generator.generate_full_pe_report_sync(
        signals, str(audit_id), audit_metadata=audit_meta, frameworks=frameworks,
    )
    report_data["audit_status"] = audit.status
    report_data["audit_scope"]["phases_completed"] = audit.current_phase

    from app.reports.pdf_generator import PEPDFReport

    pdf_gen = PEPDFReport()
    pdf_bytes = pdf_gen.generate_pdf(report_data, company_name=company)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="DeepAudit_DD_Report_{audit_id}.pdf"',
        },
    )


@router.get("/{audit_id}/scalability")
async def get_scalability_assessment(
    audit_id: uuid.UUID,
    tenant: Tenant = Depends(_authenticate_by_key),
    db: AsyncSession = Depends(get_db),
):
    """Scalability assessment with 2x/5x/10x growth scenarios."""
    audit, signals = await _load_audit_signals(db, audit_id, tenant.id)
    return _generator.generate_scalability_assessment(signals)
