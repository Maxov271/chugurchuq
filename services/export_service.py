"""
services/export_service.py
-----------------------------
Hisobotlarni TXT, CSV, XLSX va PDF formatlarida professional ko'rinishda
eksport qilish. pandas — jadval ma'lumotlarini tayyorlash uchun,
reportlab — PDF generatsiyasi uchun ishlatiladi.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from config import settings
from database.connection import db
from database.queries import export_repo
from utils.logger import get_logger

logger = get_logger(__name__)

FILTER_QUERIES = {
    "today": "SELECT * FROM messages WHERE report_date = date('now') ORDER BY id DESC",
    "weekly": "SELECT * FROM messages WHERE report_date >= date('now', '-7 days') ORDER BY id DESC",
    "monthly": "SELECT * FROM messages WHERE report_date >= date('now', '-30 days') ORDER BY id DESC",
    "all": "SELECT * FROM messages ORDER BY id DESC",
    "unread": "SELECT * FROM messages WHERE is_read = 0 ORDER BY id DESC",
}

COLUMNS = ["internal_id", "report_date", "report_time", "report_type", "media_type", "status", "is_read", "is_replied"]
COLUMN_LABELS = ["ID", "Sana", "Vaqt", "Turi", "Media", "Status", "O'qilgan", "Javob berilgan"]


class ExportService:
    async def _fetch_rows(self, filter_type: str) -> list[dict]:
        query = FILTER_QUERIES.get(filter_type, FILTER_QUERIES["all"])
        rows = await db.fetch_all(query)
        return [dict(r) for r in rows]

    def _to_dataframe(self, rows: list[dict]) -> pd.DataFrame:
        df = pd.DataFrame(rows)
        if df.empty:
            return pd.DataFrame(columns=COLUMNS)
        df = df[COLUMNS]
        df["is_read"] = df["is_read"].map({1: "Ha", 0: "Yo'q"})
        df["is_replied"] = df["is_replied"].map({1: "Ha", 0: "Yo'q"})
        df.columns = COLUMN_LABELS
        return df

    def _timestamped_path(self, ext: str) -> Path:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return settings.exports_dir / f"hisobot_{stamp}.{ext}"

    async def export_txt(self, filter_type: str, admin_id: int) -> Path:
        rows = await self._fetch_rows(filter_type)
        path = self._timestamped_path("txt")
        lines = [f"Hisobotlar eksporti — filtr: {filter_type}", "=" * 40]
        for r in rows:
            lines.append(
                f"{r['internal_id']} | {r['report_date']} {r['report_time']} | "
                f"{r['report_type']} | {r['media_type']} | status={r['status']}"
            )
        path.write_text("\n".join(lines), encoding="utf-8")
        await export_repo.log(admin_id, "txt", filter_type, str(path))
        return path

    async def export_csv(self, filter_type: str, admin_id: int) -> Path:
        rows = await self._fetch_rows(filter_type)
        df = self._to_dataframe(rows)
        path = self._timestamped_path("csv")
        df.to_csv(path, index=False, encoding="utf-8-sig")
        await export_repo.log(admin_id, "csv", filter_type, str(path))
        return path

    async def export_xlsx(self, filter_type: str, admin_id: int) -> Path:
        rows = await self._fetch_rows(filter_type)
        df = self._to_dataframe(rows)
        path = self._timestamped_path("xlsx")

        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Hisobotlar")
            worksheet = writer.sheets["Hisobotlar"]
            for i, col in enumerate(df.columns, start=1):
                max_len = max(df[col].astype(str).map(len).max() if not df.empty else 0, len(col)) + 4
                worksheet.column_dimensions[worksheet.cell(row=1, column=i).column_letter].width = max_len

        await export_repo.log(admin_id, "xlsx", filter_type, str(path))
        return path

    async def export_pdf(self, filter_type: str, admin_id: int) -> Path:
        rows = await self._fetch_rows(filter_type)
        df = self._to_dataframe(rows)
        path = self._timestamped_path("pdf")

        doc = SimpleDocTemplate(str(path), pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("TitleUZ", parent=styles["Title"], fontSize=16)

        elements = [
            Paragraph(f"Hisobotlar — filtr: {filter_type}", title_style),
            Spacer(1, 0.5 * cm),
        ]

        table_data = [list(df.columns)] + df.astype(str).values.tolist()
        if len(table_data) == 1:
            table_data.append(["—"] * len(df.columns))

        table = Table(table_data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E4053")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F3F4")]),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        elements.append(table)
        doc.build(elements)

        await export_repo.log(admin_id, "pdf", filter_type, str(path))
        return path


export_service = ExportService()
