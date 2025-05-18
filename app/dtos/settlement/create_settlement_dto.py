from decimal import Decimal
from pydantic import BaseModel

class CreateSettlementDto(BaseModel):
  visa_net_report_date: str
  visa_net_settlement_amount: Decimal
  visa_net_transaction_count: int
  visa_net_report_fileName: str
  email_id: str | None
  attachment_id: str | None

  def to_dict(self):
    return {
      "visa_net_report_date": self.visa_net_report_date,
      "visa_net_settlement_amount": self.visa_net_settlement_amount,
      "visa_net_transaction_count": self.visa_net_transaction_count,
      "visa_net_report_fileName": self.visa_net_report_fileName,
      "email_id": self.email_id,
      "attachment_id": self.attachment_id
    }