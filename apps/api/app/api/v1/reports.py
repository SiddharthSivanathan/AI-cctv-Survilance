"""Report endpoints (tenant-scoped): list, generate, view, PDF/CSV export."""

from __future__ import annotations

import uuid

import httpx
from fastapi import APIRouter, Depends, Response, status

from app.core.deps import AuthContext, get_report_service, require_membership
from app.schemas.report import (
    GenerateReportRequest,
    ReportData,
    ReportListItem,
    ReportResponse,
)
from app.services import ReportService
from app.services.report_csv import build_report_csv
from app.services.report_pdf import build_report_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


def _org(ctx: AuthContext) -> uuid.UUID:
    return ctx.membership.organization_id  # type: ignore[union-attr]


@router.get("", response_model=list[ReportListItem])
async def list_reports(
    ctx: AuthContext = Depends(require_membership),
    service: ReportService = Depends(get_report_service),
) -> list[ReportListItem]:
    reports = await service.list(_org(ctx))
    return [ReportListItem.model_validate(r) for r in reports]


@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    payload: GenerateReportRequest,
    ctx: AuthContext = Depends(require_membership),
    service: ReportService = Depends(get_report_service),
) -> ReportResponse:
    report = await service.generate(
        _org(ctx), report_type=payload.report_type, end_date=payload.end_date
    )
    return ReportResponse.model_validate(report)


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: uuid.UUID,
    ctx: AuthContext = Depends(require_membership),
    service: ReportService = Depends(get_report_service),
) -> ReportResponse:
    return ReportResponse.model_validate(await service.get(report_id, _org(ctx)))


@router.get("/{report_id}/pdf")
async def download_pdf(
    report_id: uuid.UUID,
    ctx: AuthContext = Depends(require_membership),
    service: ReportService = Depends(get_report_service),
) -> Response:
    report = await service.get(report_id, _org(ctx))
    data = ReportData.model_validate(report.data)
    logo_bytes = await _fetch_logo(data.logo_url)
    pdf = build_report_pdf(data, logo_bytes=logo_bytes)
    filename = f"{data.report_type}-report-{data.end_date}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{report_id}/csv")
async def download_csv(
    report_id: uuid.UUID,
    ctx: AuthContext = Depends(require_membership),
    service: ReportService = Depends(get_report_service),
) -> Response:
    report = await service.get(report_id, _org(ctx))
    data = ReportData.model_validate(report.data)
    csv_text = build_report_csv(data)
    filename = f"{data.report_type}-report-{data.end_date}.csv"
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def _fetch_logo(logo_url: str | None) -> bytes | None:
    if not logo_url:
        return None
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(logo_url)
            resp.raise_for_status()
            return resp.content
    except httpx.HTTPError:
        return None
