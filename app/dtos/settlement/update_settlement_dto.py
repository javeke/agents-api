from decimal import Decimal
from pydantic import BaseModel

class UpdateSettlementDto(BaseModel):
  visa_net_report_date: str
  fac_report_file_name: str | None
  fac_report_start_date: str | None
  fac_report_end_date: str | None
  fac_report_transaction_count: int | None
  fac_report_transaction_total: Decimal | None