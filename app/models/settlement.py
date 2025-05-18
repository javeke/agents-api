from app.enums.settlement_status import SettlementStatus
from ..db import Base
from sqlalchemy import DateTime, Column, Integer, String, Text, Numeric, Date, Time, Enum as SQLAEnum
from sqlalchemy.sql import func

class SettlementModel(Base):
  __tablename__ = "settlement"

  id = Column(Integer, primary_key=True)
  name = Column(String(100))
  description = Column(Text)
  created_at = Column(DateTime(timezone=True), default=func.now())
  last_attempt_at = Column(DateTime(timezone=True), default=func.now())
  attemps = Column(Integer, default=0)
  settlement_amount = Column(Numeric(precision=16, scale=2), nullable=True)
  settlement_date = Column(Date, nullable=True, unique=True)
  settlement_transaction_count = Column(Integer, nullable=True)
  email_id = Column(String(255), nullable=True)
  attachment_id = Column(String(255), nullable=True)

  visa_net_report_file_name = Column(String(255), nullable=True)
  fac_report_file_name = Column(String(255), nullable=True)

  fac_start_date = Column(Date, nullable=True)
  fac_start_time = Column(Time, nullable=True)
  fac_end_date = Column(Date, nullable=True)
  fac_end_time = Column(Time, nullable=True)

  fac_report_transaction_count = Column(Integer)
  fac_report_transaction_total = Column(Numeric(precision=16, scale=2))
  settlement_status: SettlementStatus = Column(SQLAEnum(SettlementStatus), nullable=False)
