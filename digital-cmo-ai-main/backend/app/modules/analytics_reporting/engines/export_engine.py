"""
Export Engine — PDF Reports, CSV Data Exports, Scheduled Email Reports

Provides multiple export formats:
  1. CSV: Raw data export for any metric set
  2. PDF: Formatted marketing report with charts and tables
  3. JSON: Structured data export
  4. Email: Scheduled report delivery via SendGrid or SMTP

Uses FPDF2 for PDF generation and standard csv module for CSV.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Optional imports
try:
    from fpdf import FPDF

    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class ExportConfig:
    """Configuration for report exports."""
    format: str = "pdf"  # "pdf", "csv", "json"
    title: str = "Marketing Analytics Report"
    subtitle: str = ""
    company_name: str = "Digital CMO AI"
    period: str = "Last 30 Days"
    include_charts: bool = True
    include_insights: bool = True
    include_benchmarks: bool = True
    output_dir: str = "/tmp/reports"


@dataclass
class EmailSchedule:
    """Configuration for scheduled email reports."""
    recipients: list[str]
    subject: str = "Weekly Marketing Report"
    frequency: str = "weekly"  # "daily", "weekly", "monthly"
    day_of_week: int = 1  # Monday=0, Sunday=6
    hour: int = 9  # UTC hour
    format: str = "pdf"
    enabled: bool = True


@dataclass
class ExportResult:
    """Result of an export operation."""
    success: bool
    format: str
    file_path: Optional[str] = None
    file_size_bytes: int = 0
    content: Optional[bytes] = None
    error: Optional[str] = None
    generated_at: str = ""


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ExportEngine:
    """Generate and export marketing reports in multiple formats."""

    def __init__(self, sendgrid_api_key: Optional[str] = None):
        self.sendgrid_api_key = sendgrid_api_key or os.environ.get("SENDGRID_API_KEY")

    def export(
        self,
        data: dict[str, Any],
        config: Optional[ExportConfig] = None,
    ) -> ExportResult:
        """
        Export analytics data in the specified format.

        Args:
            data: Dict containing metrics, insights, forecasts, etc.
            config: Export configuration.

        Returns:
            ExportResult with file path or content.
        """
        config = config or ExportConfig()
        os.makedirs(config.output_dir, exist_ok=True)

        dispatch = {
            "csv": self._export_csv,
            "json": self._export_json,
            "pdf": self._export_pdf,
        }

        fn = dispatch.get(config.format, self._export_json)
        try:
            return fn(data, config)
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return ExportResult(
                success=False,
                format=config.format,
                error=str(e),
                generated_at=datetime.now(timezone.utc).isoformat(),
            )

    # ------------------------------------------------------------------
    # CSV Export
    # ------------------------------------------------------------------

    def _export_csv(self, data: dict[str, Any], config: ExportConfig) -> ExportResult:
        """Export metrics as CSV."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"analytics_report_{timestamp}.csv"
        filepath = os.path.join(config.output_dir, filename)

        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow(["Marketing Analytics Report"])
            writer.writerow([f"Period: {config.period}"])
            writer.writerow([f"Generated: {datetime.now(timezone.utc).isoformat()}"])
            writer.writerow([])

            # Metrics section
            metrics = data.get("metrics", {})
            if metrics:
                writer.writerow(["=== KPI Metrics ==="])
                writer.writerow(["Metric", "Value"])
                for key, value in sorted(metrics.items()):
                    if not isinstance(value, dict):
                        writer.writerow([key, value])
                writer.writerow([])

            # Forecasts section
            forecast = data.get("forecast", {})
            if forecast:
                writer.writerow(["=== Forecast ==="])
                writer.writerow(["Date", "Predicted", "Lower Bound", "Upper Bound"])
                for pred in forecast.get("predictions", []):
                    writer.writerow([
                        pred.get("date", ""),
                        pred.get("predicted", ""),
                        pred.get("lower_bound", ""),
                        pred.get("upper_bound", ""),
                    ])
                writer.writerow([])

            # Attribution section
            attribution = data.get("attribution", {})
            if attribution:
                writer.writerow(["=== Attribution ==="])
                writer.writerow(["Channel", "Attributed Value", "Conversions", "ROAS"])
                scores = attribution.get("channel_scores", {})
                convs = attribution.get("channel_conversions", {})
                roas = attribution.get("channel_roas", {})
                for ch in sorted(scores.keys()):
                    writer.writerow([
                        ch,
                        scores.get(ch, 0),
                        convs.get(ch, 0),
                        roas.get(ch, 0),
                    ])
                writer.writerow([])

            # Anomalies section
            anomalies = data.get("anomalies", [])
            if anomalies:
                writer.writerow(["=== Anomalies ==="])
                writer.writerow(["Metric", "Severity", "Current", "Expected", "Message"])
                for a in anomalies:
                    writer.writerow([
                        a.get("metric", ""),
                        a.get("severity", ""),
                        a.get("current_value", ""),
                        a.get("expected_value", ""),
                        a.get("message", ""),
                    ])

        file_size = os.path.getsize(filepath)
        return ExportResult(
            success=True,
            format="csv",
            file_path=filepath,
            file_size_bytes=file_size,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------
    # JSON Export
    # ------------------------------------------------------------------

    def _export_json(self, data: dict[str, Any], config: ExportConfig) -> ExportResult:
        """Export full analytics data as JSON."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"analytics_report_{timestamp}.json"
        filepath = os.path.join(config.output_dir, filename)

        export_data = {
            "report": {
                "title": config.title,
                "company": config.company_name,
                "period": config.period,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
            "data": data,
        }

        with open(filepath, "w") as f:
            json.dump(export_data, f, indent=2, default=str)

        file_size = os.path.getsize(filepath)
        return ExportResult(
            success=True,
            format="json",
            file_path=filepath,
            file_size_bytes=file_size,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------
    # PDF Export
    # ------------------------------------------------------------------

    def _export_pdf(self, data: dict[str, Any], config: ExportConfig) -> ExportResult:
        """Export formatted PDF report."""
        if not HAS_FPDF:
            return ExportResult(
                success=False,
                format="pdf",
                error="fpdf2 not installed. Install with: pip install fpdf2",
                generated_at=datetime.now(timezone.utc).isoformat(),
            )

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"analytics_report_{timestamp}.pdf"
        filepath = os.path.join(config.output_dir, filename)

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        # --- Title Page ---
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 24)
        pdf.cell(0, 40, "", ln=True)
        pdf.cell(0, 15, config.title, ln=True, align="C")
        pdf.set_font("Helvetica", "", 14)
        if config.subtitle:
            pdf.cell(0, 10, config.subtitle, ln=True, align="C")
        pdf.cell(0, 10, f"Period: {config.period}", ln=True, align="C")
        pdf.cell(0, 10, config.company_name, ln=True, align="C")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(
            0, 10,
            f"Generated: {datetime.now(timezone.utc).strftime('%B %d, %Y %H:%M UTC')}",
            ln=True, align="C",
        )

        # --- Executive Summary ---
        summary = data.get("executive_summary", "")
        if summary:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, "Executive Summary", ln=True)
            pdf.ln(5)
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 6, summary)
            pdf.ln(5)

        # --- KPI Metrics ---
        metrics = data.get("metrics", {})
        if metrics:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, "Key Performance Indicators", ln=True)
            pdf.ln(5)

            # Table header
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_fill_color(41, 128, 185)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(95, 8, "Metric", border=1, fill=True)
            pdf.cell(95, 8, "Value", border=1, fill=True, ln=True)
            pdf.set_text_color(0, 0, 0)

            pdf.set_font("Helvetica", "", 10)
            fill = False
            for key, value in sorted(metrics.items()):
                if isinstance(value, dict):
                    continue
                if fill:
                    pdf.set_fill_color(235, 245, 251)
                display_name = key.replace("_", " ").title()
                pdf.cell(95, 7, display_name, border=1, fill=fill)
                pdf.cell(95, 7, str(value), border=1, fill=fill, ln=True)
                fill = not fill

        # --- Insights ---
        insights = data.get("insights", [])
        if insights and config.include_insights:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, "Key Insights & Recommendations", ln=True)
            pdf.ln(5)

            for i, insight in enumerate(insights, 1):
                severity = insight.get("severity", "info")
                if severity == "critical":
                    pdf.set_fill_color(231, 76, 60)
                elif severity == "warning":
                    pdf.set_fill_color(243, 156, 18)
                elif severity == "positive":
                    pdf.set_fill_color(39, 174, 96)
                else:
                    pdf.set_fill_color(52, 152, 219)

                pdf.set_text_color(255, 255, 255)
                pdf.set_font("Helvetica", "B", 11)
                title = insight.get("title", f"Insight {i}")
                pdf.cell(0, 8, f"  {severity.upper()}: {title}", ln=True, fill=True)
                pdf.set_text_color(0, 0, 0)

                pdf.set_font("Helvetica", "", 10)
                narrative = insight.get("narrative", "")
                if narrative:
                    pdf.multi_cell(0, 6, narrative)

                actions = insight.get("suggested_actions", [])
                if actions:
                    pdf.set_font("Helvetica", "I", 10)
                    pdf.cell(0, 6, "Recommended Actions:", ln=True)
                    pdf.set_font("Helvetica", "", 10)
                    for action in actions:
                        pdf.cell(10, 6, "")
                        pdf.multi_cell(0, 6, f"  * {action}")
                pdf.ln(5)

        # --- Anomalies ---
        anomalies = data.get("anomalies", [])
        if anomalies:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, "Anomaly Alerts", ln=True)
            pdf.ln(5)

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_fill_color(41, 128, 185)
            pdf.set_text_color(255, 255, 255)
            col_widths = [35, 22, 25, 25, 83]
            headers = ["Metric", "Severity", "Current", "Expected", "Details"]
            for header, w in zip(headers, col_widths):
                pdf.cell(w, 8, header, border=1, fill=True)
            pdf.ln()
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 8)

            for a in anomalies:
                pdf.cell(col_widths[0], 7, str(a.get("metric", ""))[:20], border=1)
                pdf.cell(col_widths[1], 7, str(a.get("severity", "")), border=1)
                pdf.cell(col_widths[2], 7, str(a.get("current_value", "")), border=1)
                pdf.cell(col_widths[3], 7, str(a.get("expected_value", "")), border=1)
                pdf.cell(col_widths[4], 7, str(a.get("message", ""))[:55], border=1)
                pdf.ln()

        # --- Benchmark Comparisons ---
        benchmarks = data.get("benchmarks", {})
        comparisons = benchmarks.get("comparisons", []) if isinstance(benchmarks, dict) else []
        if comparisons and config.include_benchmarks:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, "Competitive Benchmarks", ln=True)
            pdf.ln(5)

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_fill_color(41, 128, 185)
            pdf.set_text_color(255, 255, 255)
            bm_widths = [30, 22, 28, 22, 28, 28, 32]
            bm_headers = ["Metric", "Yours", "Ind. Avg", "Rank", "Gap", "Best", "Assessment"]
            for header, w in zip(bm_headers, bm_widths):
                pdf.cell(w, 8, header, border=1, fill=True)
            pdf.ln()
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 8)

            for c in comparisons:
                pdf.cell(bm_widths[0], 7, str(c.get("metric", ""))[:18], border=1)
                pdf.cell(bm_widths[1], 7, str(c.get("your_value", "")), border=1)
                pdf.cell(bm_widths[2], 7, str(c.get("industry_avg", "")), border=1)
                pdf.cell(bm_widths[3], 7, f"{c.get('percentile_rank', 0)}%", border=1)
                pdf.cell(bm_widths[4], 7, str(c.get("gap_to_avg", "")), border=1)
                pdf.cell(bm_widths[5], 7, str(c.get("best_in_class", "")), border=1)
                pdf.cell(bm_widths[6], 7, str(c.get("assessment", "")), border=1)
                pdf.ln()

        # Save PDF
        pdf.output(filepath)
        file_size = os.path.getsize(filepath)

        return ExportResult(
            success=True,
            format="pdf",
            file_path=filepath,
            file_size_bytes=file_size,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------
    # Email Delivery
    # ------------------------------------------------------------------

    async def send_email_report(
        self,
        export_result: ExportResult,
        schedule: EmailSchedule,
    ) -> dict[str, Any]:
        """
        Send an exported report via email.

        Args:
            export_result: The exported report file.
            schedule: Email configuration.

        Returns:
            Dict with send status.
        """
        if not self.sendgrid_api_key:
            return {
                "success": False,
                "error": "SendGrid API key not configured.",
            }

        if not HAS_HTTPX:
            return {
                "success": False,
                "error": "httpx not installed for email delivery.",
            }

        if not export_result.success or not export_result.file_path:
            return {
                "success": False,
                "error": "No valid export file to send.",
            }

        try:
            import base64

            with open(export_result.file_path, "rb") as f:
                file_content = base64.b64encode(f.read()).decode()

            filename = os.path.basename(export_result.file_path)
            mime_type = {
                "pdf": "application/pdf",
                "csv": "text/csv",
                "json": "application/json",
            }.get(export_result.format, "application/octet-stream")

            payload = {
                "personalizations": [
                    {"to": [{"email": r} for r in schedule.recipients]}
                ],
                "from": {"email": "reports@digitalcmo.ai", "name": "Digital CMO AI"},
                "subject": schedule.subject,
                "content": [
                    {
                        "type": "text/html",
                        "value": (
                            f"<h2>{schedule.subject}</h2>"
                            f"<p>Please find your scheduled marketing analytics report attached.</p>"
                            f"<p>Generated: {datetime.now(timezone.utc).strftime('%B %d, %Y %H:%M UTC')}</p>"
                            f"<p><em>This is an automated report from Digital CMO AI.</em></p>"
                        ),
                    }
                ],
                "attachments": [
                    {
                        "content": file_content,
                        "filename": filename,
                        "type": mime_type,
                        "disposition": "attachment",
                    }
                ],
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.sendgrid_api_key}",
                        "Content-Type": "application/json",
                    },
                )

            return {
                "success": response.status_code in (200, 202),
                "status_code": response.status_code,
                "recipients": schedule.recipients,
                "sent_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return {"success": False, "error": str(e)}
