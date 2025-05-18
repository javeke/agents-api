from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from os import path
import re
from pathlib import Path

from fastapi import Depends
from app.services.report_processing.report_service import ReportService
from app.dependencies import get_report_service
import pdfplumber 
import logging

logging.getLogger("pdfminer").setLevel(logging.ERROR)

REPORT_ID_RE      = re.compile(r"REPORT\s+ID:\s*VSS-120", re.I)
SETTLEMENT_RE     = re.compile(r"SETTLEMENT\s+CURRENCY:\s*TTD", re.I)
CLEARING_RE       = re.compile(r"CLEARING\s+CURRENCY:\s*TTD", re.I)
ROW_LABEL         = "ORIGINAL SALE"
TITLE_RE       = re.compile(r"INTERCHANGE\s+VALUE\s+REPORT",    re.I)
ROW_RE            = re.compile(rf"{ROW_LABEL}\s+([\d,]+)\s+([\d,]+\.\d{{2}})")
DATE_RE = re.compile(
  r"REPORT\s+DATE\s*:\s*([0-9]{1,2}\s*[A-Z]{3}\s*[0-9]{2,4})",
  re.I
)

def __normalise_date(raw: str) -> date | None:
  """
  Convert many common VisaNet date formats to a datetime.date.
  e.g. '07 MAY 2025', '7 May 2025', '05/07/2025', '07-05-2025',06MAY25
  """
  raw = raw.strip().replace("\u2011", "-")
  fmt_variants = ["%d %b %Y", "%d %B %Y", "%d/%m/%Y", "%d-%m-%Y", "%d%b%y", "%d%b%Y"]
  for fmt in fmt_variants:
    try:
      return datetime.strptime(raw, fmt).date()
    except ValueError:
      continue
  return None


def __find_page_text(pdf_path: Path) -> str | None:
  with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
      text = page.extract_text() or ""
      if (REPORT_ID_RE.search(text)
            and SETTLEMENT_RE.search(text)
            and CLEARING_RE.search(text)
            and TITLE_RE.search(text)):
          return text
    logging.info("Unable to locate report page")
    return None


def __extract_original_sale(page_text: str) -> tuple[int, Decimal, date] | None:
  """
  Return (count, amount) from the ORIGINAL SALE row, or None if not found.
  """
  date_match = DATE_RE.search(page_text)
  if not date_match:
      return None
  report_date = __normalise_date(date_match.group(1))
  if not report_date:
      return None
  m = ROW_RE.search(page_text)
  if not m:
    logging.info("Unable to find original sale row")
    return 0, 0.00, report_date
  
  count  = int(m.group(1).replace(",", ""))
  raw_amount = m.group(2).replace(",", "")
  try:
    amount = Decimal(raw_amount)
  except InvalidOperation:
    logging.info("Unable to get clearing amount")
    return None
  
  return count, amount, report_date


def extract_visa_net_data(pdf_file: str) -> tuple[int, Decimal, date] | None:
  logging.info(f"Visa net file name {pdf_file}")
  if not pdf_file.endswith('.pdf'):
    pdf_file = f"{pdf_file}.pdf"

  report_service: ReportService = get_report_service()
  file_path = report_service.get_visa_net_file_path(pdf_file)

  if not path.exists(file_path):
    logging.info(f"Visa net file {pdf_file} does not exist as {file_path}")
    return None

  page_text = __find_page_text(Path(file_path))
  if page_text is None:
      return None

  result = __extract_original_sale(page_text)
  if result is None:
    return None

  count, amount, report_date = result

  return count, amount, report_date


def extract_visa_net_data_tool_definition() -> dict:
  return {
    "type": "function",
    "function": {
      "name": "extract_visa_net_data",
      "description": "Extracts the visa net transaction count, visa net transaction total, report date from the visa net pdf report for report VSS 120 and settlement currency TTD",
      "parameters": {
        "type": "object",
        "properties": {
          "visaNetReportFileName": {
            "type": "string",
            "description": "The unmodified file name of the VisaNet report file being settled. eg. TT Acquirer Visa Files 07.05.2025.pdf",
            "nullable": False
          },
        },
        "required": [
          "visaNetReportFileName"
        ]
      }
    }
  }