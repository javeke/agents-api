from sqlalchemy import select
from app.dtos.settlement.create_settlement_dto import CreateSettlementDto
from app.dtos.settlement.update_settlement_dto import UpdateSettlementDto
from app.enums.settlement_status import SettlementStatus
from app.exceptions.settlement_exceptions import SettlementAlreadyCompletedError
from app.models.settlement import SettlementModel
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

class SettlementService:
  def __init__(self, db: AsyncSession):
    self.db = db

  async def create_settlement(self, dto: CreateSettlementDto):
    settlement_date = datetime.strptime(dto.visa_net_report_date, "%Y-%m-%d").date()
    settlement_total = dto.visa_net_settlement_amount
    settlement_count = dto.visa_net_transaction_count
    visa_net_report_file_name = dto.visa_net_report_fileName

    settlement_model = SettlementModel(
      name=f"Settlement for {dto.visa_net_report_date}",
      description=f"Settlement for {dto.visa_net_report_date}",settlement_date=settlement_date,
      settlement_transaction_count=settlement_count, settlement_amount=settlement_total,
      visa_net_report_file_name=visa_net_report_file_name, settlement_status=SettlementStatus.New
    )
    query = select(SettlementModel).where(SettlementModel.settlement_date == settlement_date).order_by(SettlementModel.id.asc()).limit(1)
    result = await self.db.execute(query)
    found = result.scalar_one_or_none()

    if not found:
      self.db.add(settlement_model)
      await self.db.commit()
      return

    if found.settlement_status == SettlementStatus.Completed:
      raise SettlementAlreadyCompletedError(f"Settlement for {found.settlement_date} was already done")


  async def update_settlement(self, dto: UpdateSettlementDto) -> None:
    settlement_date = datetime.strptime(dto.visa_net_report_date, "%Y-%m-%d").date()
    
    query = select(SettlementModel).where(SettlementModel.settlement_date == settlement_date).order_by(SettlementModel.id.asc()).limit(1)
    result = await self.db.execute(query)
    
    settlement_model: SettlementModel | None = result.scalar_one_or_none()

    if not settlement_model:
      raise ValueError("Settlement record does not exist")
    
    if settlement_model.settlement_status == SettlementStatus.Completed:
      raise SettlementAlreadyCompletedError(f"Settlement for {settlement_model.settlement_date} was already done")
    
    if dto.fac_report_start_date:
      settlement_model.fac_start_date = datetime.strptime(dto.fac_report_start_date, "%Y-%m-%d").date()
    
    if dto.fac_report_end_date:
      settlement_model.fac_end_date = datetime.strptime(dto.fac_report_end_date, "%Y-%m-%d").date()

    if dto.fac_report_transaction_count:
      settlement_model.fac_report_transaction_count = dto.fac_report_transaction_count

    if dto.fac_report_transaction_total:
      settlement_model.fac_report_transaction_total = dto.fac_report_transaction_total

    if dto.fac_report_file_name:
      settlement_model.fac_report_file_name = dto.fac_report_file_name

    settlement_model.fac_start_date = settlement_date
    settlement_model.settlement_status = SettlementStatus.Completed

    await self.db.commit()