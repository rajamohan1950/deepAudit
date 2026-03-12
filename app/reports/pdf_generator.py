"""PDF report generator — produces PE-quality PDF deliverables."""

from __future__ import annotations

import io
import unicodedata
from datetime import datetime, timezone
from typing import Any

from fpdf import FPDF


def _latin1_safe(text: str) -> str:
    """Replace Unicode characters that Helvetica/Latin-1 can't encode."""
    if not text:
        return ""
    replacements = {
        "\u2014": "--",   # em dash
        "\u2013": "-",    # en dash
        "\u2018": "'",    # left single quote
        "\u2019": "'",    # right single quote
        "\u201c": '"',    # left double quote
        "\u201d": '"',    # right double quote
        "\u2026": "...",  # ellipsis
        "\u2022": "*",    # bullet
        "\u00a0": " ",    # non-breaking space
        "\u200b": "",     # zero-width space
        "\u2003": " ",    # em space
        "\u2002": " ",    # en space
        "\u2192": "->",   # right arrow
        "\u2190": "<-",   # left arrow
        "\u2265": ">=",   # ≥
        "\u2264": "<=",   # ≤
        "\u2260": "!=",   # ≠
        "\u00b7": ".",    # middle dot
    }
    for uchar, replacement in replacements.items():
        text = text.replace(uchar, replacement)
    # Fallback: encode to latin-1, replacing anything still unknown
    return text.encode("latin-1", errors="replace").decode("latin-1")

_DARK = (30, 36, 50)
_WHITE = (255, 255, 255)
_LIGHT_GRAY = (240, 240, 245)
_MEDIUM_GRAY = (160, 165, 175)
_TEXT = (50, 55, 65)

_RED = (220, 53, 69)
_ORANGE = (230, 126, 34)
_YELLOW = (200, 170, 30)
_GREEN = (40, 167, 69)
_BLUE = (41, 98, 255)

_SEVERITY_COLORS = {
    "P0": _RED,
    "P1": _ORANGE,
    "P2": _YELLOW,
    "P3": _GREEN,
}

_HEATMAP_STATUS_COLORS = {
    "red": _RED,
    "orange": _ORANGE,
    "yellow": _YELLOW,
    "green": _GREEN,
}

_TRAFFIC_BG = {
    "Red": _RED,
    "Amber": _ORANGE,
    "Green": _GREEN,
}


class PEPDFReport(FPDF):
    """Generates professional PE-grade due-diligence PDF reports."""

    _company: str = "Target Company"
    _report_id: str = ""
    _generated_at: str = ""

    def cell(self, w=None, h=None, text="", *args, **kwargs):
        """Override to auto-sanitize Unicode text for Latin-1 Helvetica font."""
        return super().cell(w, h, _latin1_safe(str(text)) if text else text, *args, **kwargs)

    def multi_cell(self, w, h=None, text="", *args, **kwargs):
        """Override to auto-sanitize Unicode text for Latin-1 Helvetica font."""
        return super().multi_cell(w, h, _latin1_safe(str(text)) if text else text, *args, **kwargs)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_fill_color(*_DARK)
        self.rect(0, 0, self.w, 14, "F")
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*_WHITE)
        self.set_xy(8, 3)
        self.cell(0, 8, "DEEPAUDIT  |  Technical Due Diligence Report", align="L")
        self.set_xy(-60, 3)
        self.cell(50, 8, f"Page {self.page_no()}", align="R")
        self.set_text_color(*_TEXT)
        self.ln(16)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*_MEDIUM_GRAY)
        self.cell(0, 10, "CONFIDENTIAL", align="C")

    # ── helpers ──────────────────────────────────────────────────

    def _section_title(self, title: str) -> None:
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*_DARK)
        self.cell(0, 10, _latin1_safe(title), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*_BLUE)
        self.set_line_width(0.7)
        self.line(self.l_margin, self.get_y(), self.l_margin + 55, self.get_y())
        self.ln(5)

    def _sub_heading(self, text: str) -> None:
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*_DARK)
        self.cell(0, 7, _latin1_safe(text), new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def _body_text(self, text: str) -> None:
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*_TEXT)
        self.multi_cell(0, 5, _latin1_safe(text))
        self.ln(2)

    def _pill(self, text: str, bg: tuple[int, int, int], w: float = 50) -> None:
        self.set_fill_color(*bg)
        self.set_text_color(*_WHITE)
        self.set_font("Helvetica", "B", 11)
        x, y = self.get_x(), self.get_y()
        self.rect(x, y, w, 9, "F")
        self.set_xy(x, y)
        self.cell(w, 9, _latin1_safe(text), align="C")
        self.set_text_color(*_TEXT)

    def _kv_row(self, label: str, value: str) -> None:
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*_MEDIUM_GRAY)
        self.cell(55, 6, _latin1_safe(label), new_x="END")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*_TEXT)
        self.cell(0, 6, _latin1_safe(value), new_x="LMARGIN", new_y="NEXT")

    def _table_header(self, widths: list[float], headers: list[str]) -> None:
        self.set_fill_color(*_DARK)
        self.set_text_color(*_WHITE)
        self.set_font("Helvetica", "B", 8)
        for w, h in zip(widths, headers):
            self.cell(w, 7, _latin1_safe(h), border=0, align="C", fill=True, new_x="END")
        self.ln()
        self.set_text_color(*_TEXT)

    def _table_row(
        self,
        widths: list[float],
        values: list[str],
        aligns: list[str] | None = None,
        fill: bool = False,
    ) -> None:
        if fill:
            self.set_fill_color(*_LIGHT_GRAY)
        self.set_font("Helvetica", "", 8)
        if aligns is None:
            aligns = ["L"] * len(values)
        for w, v, a in zip(widths, values, aligns):
            self.cell(w, 6, _latin1_safe(v[:60]), border=0, align=a, fill=fill, new_x="END")
        self.ln()

    def _ensure_space(self, h: float = 30) -> None:
        if self.get_y() + h > self.h - 20:
            self.add_page()

    # ── pages ────────────────────────────────────────────────────

    def _cover_page(self, data: dict, company: str) -> None:
        self.add_page()

        self.set_fill_color(*_DARK)
        self.rect(0, 0, self.w, 110, "F")

        self.set_font("Helvetica", "B", 36)
        self.set_text_color(*_WHITE)
        self.set_xy(0, 30)
        self.cell(self.w, 14, "DEEPAUDIT", align="C", new_x="LMARGIN", new_y="NEXT")

        self.set_font("Helvetica", "", 16)
        self.set_xy(0, 52)
        self.cell(self.w, 10, "Technical Due Diligence Report", align="C", new_x="LMARGIN", new_y="NEXT")

        self.set_draw_color(*_BLUE)
        self.set_line_width(1)
        mid = self.w / 2
        self.line(mid - 40, 70, mid + 40, 70)

        self.set_font("Helvetica", "I", 12)
        self.set_text_color(200, 205, 215)
        self.set_xy(0, 78)
        self.cell(self.w, 8, _latin1_safe(f"CONFIDENTIAL -- Prepared for {company}"), align="C")

        self.set_font("Helvetica", "", 11)
        self.set_text_color(*_MEDIUM_GRAY)
        self.set_xy(0, 96)
        self.cell(self.w, 8, f"Generated  {self._generated_at[:10]}", align="C")

        self.set_text_color(*_TEXT)
        self.set_y(125)
        audit_id = data.get("audit_id", self._report_id)
        self._kv_row("Report ID:", audit_id)
        scope = data.get("audit_scope", {})
        self._kv_row("Total Signals:", str(scope.get("total_signals", "—")))
        self._kv_row("Phases Completed:", str(scope.get("phases_completed", "—")))
        self._kv_row("Report Version:", data.get("report_version", "2.0"))

    def _executive_summary_page(self, es: dict) -> None:
        self.add_page()
        self._section_title("Executive Summary")

        score = es.get("overall_risk_score", 0)
        light = es.get("traffic_light", "Green")
        rec = es.get("recommendation", "")

        self._sub_heading("Overall Assessment")
        self._kv_row("Risk Score:", f"{score} / 100")
        self.set_x(self.l_margin + 55)
        self._pill(light, _TRAFFIC_BG.get(light, _GREEN), w=35)
        self.ln(4)
        self._kv_row("Recommendation:", rec)

        sev = es.get("severity_breakdown", {})
        self._kv_row("Signals:", f"P0={sev.get('P0',0)}  P1={sev.get('P1',0)}  P2={sev.get('P2',0)}  P3={sev.get('P3',0)}  (Total {es.get('total_signals',0)})")
        hours = es.get("estimated_total_remediation_hours", 0)
        cost = es.get("estimated_total_remediation_cost_usd", 0)
        self._kv_row("Remediation Effort:", f"{hours:,} hrs  (~${cost:,.0f})")
        self.ln(5)

        self._sub_heading("Top 5 Critical Findings")
        widths = [8, 62, 14, 12, 55, 40]
        self._table_header(widths, ["#", "Finding", "Sev", "Score", "Evidence", "Remediation"])
        for i, f in enumerate(es.get("top_5_critical_findings", [])):
            self._table_row(
                widths,
                [
                    str(f.get("rank", i + 1)),
                    f.get("signal", "")[:60],
                    f.get("severity", ""),
                    str(f.get("score", "")),
                    f.get("evidence", "")[:55],
                    f.get("remediation", "")[:40],
                ],
                aligns=["C", "L", "C", "C", "L", "L"],
                fill=i % 2 == 0,
            )

    def _risk_heatmap_page(self, hm: dict) -> None:
        self.add_page()
        self._section_title("Risk Heatmap")
        self._body_text(
            "Each of the 40 audit categories is scored and color-coded by severity. "
            "Red = P0 present, Orange = multiple P1, Yellow = P1 or clustered P2, Green = low/no issues."
        )
        widths = [55, 18, 22, 18, 18]
        self._table_header(widths, ["Category", "Signals", "Max Severity", "Score", "Status"])

        matrix = hm.get("matrix", {})
        row_idx = 0
        for cat_id in sorted(matrix, key=lambda k: int(k)):
            entry = matrix[cat_id]
            if entry.get("signal_count", 0) == 0:
                continue
            self._ensure_space(8)
            color_key = entry.get("color", "green")
            sev_color = _HEATMAP_STATUS_COLORS.get(color_key, _GREEN)

            self.set_font("Helvetica", "", 8)
            self.set_text_color(*_TEXT)
            if row_idx % 2 == 0:
                self.set_fill_color(*_LIGHT_GRAY)
            else:
                self.set_fill_color(*_WHITE)
            fill = row_idx % 2 == 0

            self.cell(55, 6, entry.get("category_name", "")[:52], fill=fill, new_x="END")
            self.cell(18, 6, str(entry.get("signal_count", 0)), align="C", fill=fill, new_x="END")
            self.cell(22, 6, entry.get("max_severity", ""), align="C", fill=fill, new_x="END")
            self.cell(18, 6, str(entry.get("risk_score", 0)), align="C", fill=fill, new_x="END")

            x_status = self.get_x()
            y_status = self.get_y()
            self.set_fill_color(*sev_color)
            self.set_text_color(*_WHITE)
            self.set_font("Helvetica", "B", 7)
            self.cell(18, 6, color_key.upper(), align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
            self.set_text_color(*_TEXT)
            row_idx += 1

    def _findings_by_severity_page(self, es: dict, hm: dict) -> None:
        self.add_page()
        self._section_title("Key Findings by Severity")

        all_findings = es.get("top_5_critical_findings", [])

        matrix = hm.get("matrix", {})
        extra: list[dict] = []
        for cat_id, entry in matrix.items():
            bd = entry.get("severity_breakdown", {})
            for sev in ("P0", "P1", "P2"):
                cnt = bd.get(sev, 0)
                if cnt > 0:
                    extra.append({
                        "signal": f"{entry.get('category_name', 'Category')} — {cnt} {sev} signal(s)",
                        "severity": sev,
                        "score": entry.get("risk_score", 0),
                        "evidence": f"Detected in category {cat_id}",
                        "remediation": "See heatmap for full breakdown",
                        "effort": "—",
                    })

        already = {f.get("signal", "")[:60] for f in all_findings}
        for e in extra:
            if e["signal"][:60] not in already:
                all_findings.append(e)

        for sev_label, sev_code, color in [
            ("P0 — Critical", "P0", _RED),
            ("P1 — High", "P1", _ORANGE),
            ("P2 — Medium", "P2", _YELLOW),
        ]:
            items = [f for f in all_findings if f.get("severity") == sev_code]
            if not items:
                continue

            self._ensure_space(20)
            self.set_fill_color(*color)
            self.set_text_color(*_WHITE)
            self.set_font("Helvetica", "B", 10)
            self.cell(0, 8, f"  {sev_label}  ({len(items)} finding{'s' if len(items) != 1 else ''})", fill=True, new_x="LMARGIN", new_y="NEXT")
            self.set_text_color(*_TEXT)
            self.ln(2)

            for f in items[:15]:
                self._ensure_space(22)
                self.set_font("Helvetica", "B", 8)
                self.cell(0, 5, f.get("signal", "")[:100], new_x="LMARGIN", new_y="NEXT")
                self.set_font("Helvetica", "", 7)
                self.set_text_color(*_MEDIUM_GRAY)
                self.cell(0, 4, f"Evidence: {f.get('evidence', '')[:120]}", new_x="LMARGIN", new_y="NEXT")
                self.set_text_color(*_TEXT)
                self.cell(0, 4, f"Remediation: {f.get('remediation', '')[:120]}  |  Effort: {f.get('effort', '—')}", new_x="LMARGIN", new_y="NEXT")
                self.ln(2)

    def _compliance_page(self, comp: dict) -> None:
        self.add_page()
        self._section_title("Compliance Readiness Overview")

        fw_results = comp.get("framework_results", {})
        if not fw_results:
            self._body_text("No compliance frameworks analyzed.")
            return

        widths = [35, 28, 20, 25, 22]
        self._table_header(widths, ["Framework", "Readiness", "Gaps", "Cost to Close", "Status"])
        row_idx = 0
        for fw, result in fw_results.items():
            self._ensure_space(8)
            readiness = result.get("readiness_score", 0)
            gaps = result.get("gap_count", 0)
            cost = result.get("cost_to_compliance_usd", 0)
            if readiness >= 80:
                status_label, status_color = "PASS", _GREEN
            elif readiness >= 50:
                status_label, status_color = "PARTIAL", _ORANGE
            else:
                status_label, status_color = "FAIL", _RED

            fill = row_idx % 2 == 0
            if fill:
                self.set_fill_color(*_LIGHT_GRAY)

            self.set_font("Helvetica", "B", 8)
            self.set_text_color(*_TEXT)
            self.cell(35, 6, fw.upper(), fill=fill, new_x="END")
            self.set_font("Helvetica", "", 8)
            self.cell(28, 6, f"{readiness}%", align="C", fill=fill, new_x="END")
            self.cell(20, 6, str(gaps), align="C", fill=fill, new_x="END")
            self.cell(25, 6, f"${cost:,.0f}", align="R", fill=fill, new_x="END")

            self.set_fill_color(*status_color)
            self.set_text_color(*_WHITE)
            self.set_font("Helvetica", "B", 7)
            self.cell(22, 6, status_label, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
            self.set_text_color(*_TEXT)
            row_idx += 1

        self.ln(6)
        total = comp.get("total_cost_to_full_compliance_usd", 0)
        self._kv_row("Total Cost to Compliance:", f"${total:,.0f}")

        cross = comp.get("cross_framework_overlap", [])
        if cross:
            self.ln(4)
            self._sub_heading("Cross-Framework Gaps")
            for item in cross[:10]:
                self._body_text(f"• {item.get('signal', '')[:80]}  →  {', '.join(item.get('frameworks', []))}")

    def _roadmap_page(self, rm: dict) -> None:
        self.add_page()
        self._section_title("Remediation Roadmap")

        phases = rm.get("phases", [])
        for phase in phases:
            self._ensure_space(25)
            label = phase.get("phase", "")
            count = phase.get("item_count", 0)
            hours = phase.get("total_hours", 0)
            cost = phase.get("total_cost_usd", 0)
            engineers = phase.get("engineers_recommended", 1)

            self.set_fill_color(*_DARK)
            self.set_text_color(*_WHITE)
            self.set_font("Helvetica", "B", 9)
            self.cell(0, 7, f"  {label}", fill=True, new_x="LMARGIN", new_y="NEXT")
            self.set_text_color(*_TEXT)
            self.ln(1)

            self.set_font("Helvetica", "", 8)
            self.cell(0, 5, f"Items: {count}   |   Hours: {hours:,}   |   Cost: ${cost:,.0f}   |   Engineers: {engineers}", new_x="LMARGIN", new_y="NEXT")
            self.ln(3)

            for item in phase.get("items", [])[:8]:
                self._ensure_space(12)
                self.set_font("Helvetica", "B", 7)
                self.cell(0, 4, f"• {item.get('signal', '')[:95]}", new_x="LMARGIN", new_y="NEXT")
                self.set_font("Helvetica", "", 7)
                self.set_text_color(*_MEDIUM_GRAY)
                self.cell(0, 4, f"  {item.get('category', '')} | {item.get('effort', '')} | {item.get('estimated_hours', 0)}h — {item.get('remediation', '')[:80]}", new_x="LMARGIN", new_y="NEXT")
                self.set_text_color(*_TEXT)
            self.ln(3)

        self.ln(4)
        res = rm.get("resource_summary", {})
        self._sub_heading("Resource Summary")
        self._kv_row("Total Engineer-Months:", str(res.get("total_engineer_months", "—")))
        self._kv_row("Recommended Team Size:", str(res.get("recommended_team_size", "—")))
        self._kv_row("Grand Total Cost:", f"${rm.get('grand_total_cost_usd', 0):,.0f}")

    def _appendix_signals_page(self, data: dict) -> None:
        self.add_page()
        self._section_title("Appendix — Signal Details")
        self._body_text("Complete listing of all signals detected during the audit.")

        deliverables = data.get("deliverables", {})
        heatmap = deliverables.get("risk_heatmap", {})
        matrix = heatmap.get("matrix", {})

        widths = [8, 38, 10, 10, 60, 50, 10]
        self._table_header(widths, ["#", "Category", "Sev", "Score", "Finding", "Remediation", "Effort"])

        row_idx = 0
        for cat_id in sorted(matrix, key=lambda k: int(k)):
            entry = matrix[cat_id]
            if entry.get("signal_count", 0) == 0:
                continue
            bd = entry.get("severity_breakdown", {})
            for sev in ("P0", "P1", "P2", "P3"):
                cnt = bd.get(sev, 0)
                for _ in range(cnt):
                    self._ensure_space(8)
                    row_idx += 1
                    self._table_row(
                        widths,
                        [
                            str(row_idx),
                            entry.get("category_name", "")[:36],
                            sev,
                            str(entry.get("risk_score", 0)),
                            f"{entry.get('category_name', '')} {sev} signal",
                            "See detailed section",
                            "—",
                        ],
                        aligns=["C", "L", "C", "C", "L", "L", "C"],
                        fill=row_idx % 2 == 0,
                    )

        roadmap = deliverables.get("remediation_roadmap", {})
        for phase in roadmap.get("phases", []):
            for item in phase.get("items", []):
                self._ensure_space(8)
                row_idx += 1
                self._table_row(
                    widths,
                    [
                        str(row_idx),
                        item.get("category", "")[:36],
                        phase.get("phase", "")[:3],
                        str(item.get("score", "")),
                        item.get("signal", "")[:58],
                        item.get("remediation", "")[:48],
                        item.get("effort", "—"),
                    ],
                    aligns=["C", "L", "C", "C", "L", "L", "C"],
                    fill=row_idx % 2 == 0,
                )

    # ── public API ───────────────────────────────────────────────

    def generate_pdf(
        self,
        report_data: dict,
        company_name: str = "Target Company",
    ) -> bytes:
        """Build a complete PE-grade PDF from the output of generate_full_pe_report_sync.

        Returns raw PDF bytes suitable for streaming via HTTP response.
        """
        self._company = company_name
        self._report_id = report_data.get("audit_id", "")
        self._generated_at = report_data.get("generated_at", datetime.now(timezone.utc).isoformat())

        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(12, 12, 12)

        deliverables = report_data.get("deliverables", {})

        self._cover_page(report_data, company_name)
        self._executive_summary_page(deliverables.get("executive_summary", {}))
        self._risk_heatmap_page(deliverables.get("risk_heatmap", {}))
        self._findings_by_severity_page(
            deliverables.get("executive_summary", {}),
            deliverables.get("risk_heatmap", {}),
        )
        self._compliance_page(deliverables.get("compliance_gap_matrix", {}))
        self._roadmap_page(deliverables.get("remediation_roadmap", {}))
        self._appendix_signals_page(report_data)

        return self.output()
