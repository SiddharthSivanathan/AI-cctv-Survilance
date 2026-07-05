"""CSV export for reports — structured metrics + tables only (no charts/summary)."""

from __future__ import annotations

import csv
import io

from app.schemas.report import ReportData


def build_report_csv(data: ReportData) -> str:
    out = io.StringIO()
    writer = csv.writer(out)

    writer.writerow(["VisionOps AI Report"])
    writer.writerow(["Company", data.company_name])
    writer.writerow(["Type", data.report_type])
    writer.writerow(["Period", f"{data.start_date} to {data.end_date}"])
    writer.writerow([])

    writer.writerow(["KPI", "Value"])
    writer.writerow(["Total footfall", data.total_footfall])
    writer.writerow(["Average occupancy", data.avg_occupancy])
    writer.writerow(["Peak occupancy", data.peak_occupancy])
    writer.writerow(["Average queue length", data.queue_stats.avg_queue_length])
    writer.writerow(["Peak queue length", data.queue_stats.peak_queue_length])
    writer.writerow(["Total alerts", data.total_alerts])
    writer.writerow(["Critical alerts", data.critical_alerts])
    writer.writerow(["Cameras online", f"{data.cameras_online}/{data.total_cameras}"])
    writer.writerow(["Overall uptime %", data.overall_uptime_pct])
    writer.writerow([])

    writer.writerow(["Camera", "Status", "Uptime %", "Footfall", "Events", "Avg occupancy", "Peak occupancy"])
    for c in data.cameras:
        writer.writerow(
            [c.camera_name, c.status, c.uptime_pct, c.total_footfall, c.total_events, c.avg_occupancy, c.peak_occupancy]
        )
    writer.writerow([])

    writer.writerow(["Time", "Camera", "Event type", "Severity", "Status"])
    for r in data.alert_rows:
        writer.writerow([r.time.isoformat(), r.camera_name, r.event_type, r.severity, r.status])

    return out.getvalue()
