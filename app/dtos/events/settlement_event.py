from pydantic import BaseModel


class SettlementEvent(BaseModel):
  email_id: str
  attachment_id: str