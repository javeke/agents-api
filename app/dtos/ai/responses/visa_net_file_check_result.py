from decimal import Decimal

from pydantic import BaseModel

class VisaNetFileNameCheckResult(BaseModel):
  """
  Return True if the string provided is similar to a visa net settlement report file name, False otherwise
  """
  is_similiar: bool

class VisaNetFileCheckResult(BaseModel):
  """
  Return True if it is a visa net settlement report, False otherwise
  """
  is_visa_net_file: bool
  file_report_date: str | None
  transaction_clearing_amount_ttd: Decimal | None
  transaction_count: int | None
