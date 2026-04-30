"""Google Sheets integration for the bank worker."""

import logging
import os
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

SHEET_COL_ANMELDECODE = 2   # B
SHEET_COL_BEZAHLT_EUR = 9  # J
SHEET_COL_TOTAL       = 8   # I
SHEET_COL_PAID        = 4   # D

COLOR_PAID_EXACT   = "#8efaab"  # grün — genau bezahlt
COLOR_PAID_OVER    = "#b7e1cd"  # hellgrün — zu viel bezahlt
COLOR_PAID_PARTIAL = "#fadc82"  # gelb — teilbezahlt

log = logging.getLogger(__name__)


def get_sheet() -> gspread.Worksheet:
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(
        Path(__file__).parent / "service_account.json", scopes=scopes
    )
    gc = gspread.authorize(creds)
    sheet_id = os.environ["GOOGLE_SHEET_ID"]
    return gc.open_by_key(sheet_id).sheet1


def _hex_to_rgb(hex_color: str) -> dict:
    h = hex_color.lstrip("#")
    return {"red": int(h[0:2], 16) / 255, "green": int(h[2:4], 16) / 255, "blue": int(h[4:6], 16) / 255}


def apply_payment_status(sheet: gspread.Worksheet, row_idx: int, paid_eur: float) -> None:
    total = float(sheet.cell(row_idx, SHEET_COL_TOTAL).value or 0)

    if paid_eur > total:
        color, is_paid = COLOR_PAID_OVER, True
    elif paid_eur == total:
        color, is_paid = COLOR_PAID_EXACT, True
    else:
        color, is_paid = COLOR_PAID_PARTIAL, False

    sheet.update_cell(row_idx, SHEET_COL_PAID, is_paid)
    sheet.format(f"A{row_idx}:K{row_idx}", {"backgroundColor": _hex_to_rgb(color)})
    log.info(f"Zahlungsstatus gesetzt: Zeile {row_idx} | paid={is_paid} | Farbe={color}")
