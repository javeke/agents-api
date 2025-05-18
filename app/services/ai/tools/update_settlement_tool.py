import json

from app.dependencies import get_db_context
from app.dtos.settlement.update_settlement_dto import UpdateSettlementDto
from app.exceptions.settlement_exceptions import SettlementAlreadyCompletedError
from app.services.settlement_processing.settlement_service import SettlementService
import logging

logger = logging.getLogger(__name__)


def update_settlement_record_tool_definition() -> dict :
  return {
    "type": "function",
    "function": {
      "name": "update_settlement_record",
      "description": "Updates an existing settlement record with new details",
      "parameters": {
        "type": "object",
        "properties": {
          "visaNetReportDate": {
            "type": "string",
            "description": "The report date from the VisaNet pdf report, in format yyyy-MM-dd. eg. 2025-04-14",
            "nullable": False
          },
          "facReportFileName":{
            "type": "string",
            "description": "The file name of the FAC report csv file generated without the file extension. eg. fac_report_05_01_2024",
            "nullable": False
          },
          "facReportStartDate":{
            "type": "string",
            "description": "The start date for the matching FAC report in format yyyy-MM-dd. eg. 2025-04-14",
            "nullable": False
          },
          "facReportEndDate":{
            "type": "string",
            "description": "The end date for the matching FAC report in format yyyy-MM-dd. eg. 2025-04-14",
            "nullable": False
          },
          "facReportTransactionCount":{
            "type": "number",
            "description": "The transaction count from the FAC report",
            "nullable": False
          },
          "facReportTransactionTotal":{
            "type": "number",
            "description": "The total of all transactions from the FAC report",
            "nullable": False
          }
        },
        "required": [
            "visaNetReportDate", "facReportFileName", 
            "facReportStartDate", "facReportEndDate", 
            "facReportTransactionCount", "facReportTransactionTotal"
        ]
      }
    }
  }

async def update_settlement_record_tool_handler(params_json: str) -> str:
  params_dict: dict = json.loads(params_json)
  visa_net_report_date = params_dict["visaNetReportDate"]
  fac_report_file_name =  params_dict.get("facReportFileName")
  fac_report_start_date =  params_dict.get("facReportStartDate")
  fac_report_end_date =  params_dict.get("facReportEndDate")
  fac_report_transaction_count =  params_dict.get("facReportTransactionCount")
  fac_report_transaction_total =  params_dict.get("facReportTransactionTotal")

  update_settlement_dto = UpdateSettlementDto(
    visa_net_report_date=visa_net_report_date,
    fac_report_file_name=fac_report_file_name,
    fac_report_start_date=fac_report_start_date,
    fac_report_end_date=fac_report_end_date,
    fac_report_transaction_count=fac_report_transaction_count,
    fac_report_transaction_total=fac_report_transaction_total
  )

  try:
    async with get_db_context() as db:
      settlement_service: SettlementService = SettlementService(db)
      await settlement_service.update_settlement(update_settlement_dto)
    return "Settlement updated successfully"
  except SettlementAlreadyCompletedError as se:
    logger.info("Settlement Already Completed", exc_info=True)
    return "Settlement Already Completed. No need to continue."
  except Exception as e:
    logger.error(msg=f"Failed to update settlement", exc_info=True)
    return "Failed to update settlement"