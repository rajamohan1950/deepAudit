import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.tenant_context import get_current_tenant
from app.models.audit import Audit
from app.models.report import Report
from app.models.tenant import Tenant
from app.schemas.report import REPORT_TYPES, ReportListResponse, ReportResponse

router = APIRouter()

VALID_REPORT_TYPES = [
    "signal-table",
    "executive-summary",
    "risk-heatmap",
    "spof-map",
    "failure-catalog",
    "performance-profile",
    "aiml-risk-register",
    "cost-analysis",
    "observability-scorecard",
    "compliance-matrix",
    "remediation-roadmap",
]


@router.get("", response_model=ReportListResponse)
async def list_reports(
    audit_id: uuid.UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    await _verify_audit_access(db, audit_id, tenant.id)

    result = await db.execute(
        select(Report).where(Report.audit_id == audit_id)
    )
    reports = result.scalars().all()

    return ReportListResponse(
        reports=[ReportResponse.model_validate(r) for r in reports]
    )


@router.get("/{report_type}", response_model=ReportResponse)
async def get_report(
    audit_id: uuid.UUID,
    report_type: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    if report_type not in VALID_REPORT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid report type. Valid types: {VALID_REPORT_TYPES}",
        )

    await _verify_audit_access(db, audit_id, tenant.id)

    result = await db.execute(
        select(Report).where(
            Report.audit_id == audit_id,
            Report.report_type == report_type,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_type}' not generated yet for this audit.",
        )
    return ReportResponse.model_validate(report)


@router.get("/{report_type}/export")
async def export_report(
    audit_id: uuid.UUID,
    report_type: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
    format: str = Query("json", description="Export format: json, csv"),
):
    if report_type not in VALID_REPORT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid report type. Valid types: {VALID_REPORT_TYPES}",
        )

    await _verify_audit_access(db, audit_id, tenant.id)

    result = await db.execute(
        select(Report).where(
            Report.audit_id == audit_id,
            Report.report_type == report_type,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_type}' not generated yet.",
        )

    if format == "json":
        return JSONResponse(
            content=report.content,
            headers={
                "Content-Disposition": f"attachment; filename={report_type}_{audit_id}.json"
            },
        )
    elif format == "csv":
        if report_type == "signal-table":
            csv_content = _signals_to_csv(report.content)
            return JSONResponse(
                content={"csv": csv_content},
                headers={
                    "Content-Disposition": f"attachment; filename={report_type}_{audit_id}.csv"
                },
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV export only supported for signal-table report.",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supported formats: json, csv",
        )


def _signals_to_csv(content: dict) -> str:
    signals = content.get("signals", [])
    if not signals:
        return ""
    headers = [
        "#", "Category", "Signal", "Severity", "Score",
        "Evidence", "Failure Scenario", "Remediation", "Effort",
    ]
    lines = [",".join(headers)]
    for s in signals:
        row = [
            str(s.get("sequence_number", "")),
            str(s.get("category_id", "")),
            f'"{s.get("signal_text", "")}"',
            s.get("severity", ""),
            str(s.get("score", "")),
            f'"{s.get("evidence", "")}"',
            f'"{s.get("failure_scenario", "")}"',
            f'"{s.get("remediation", "")}"',
            s.get("effort", ""),
        ]
        lines.append(",".join(row))
    return "\n".join(lines)


async def _verify_audit_access(
    db: AsyncSession, audit_id: uuid.UUID, tenant_id: uuid.UUID
) -> None:
    result = await db.execute(
        select(Audit.id).where(Audit.id == audit_id, Audit.tenant_id == tenant_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found.")
