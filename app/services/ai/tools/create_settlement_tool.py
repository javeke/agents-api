import json

from app.dtos.settlement.create_settlement_dto import CreateSettlementDto
from app.exceptions.settlement_exceptions import SettlementAlreadyCompletedError
from app.services.settlement_processing.settlement_service import SettlementService
from app.dependencies import get_db_context
import logging

logger = logging.getLogger(__name__)


def create_settlement_record_tool_definition() -> dict :
  return {
    "type": "function",
    "function": {
      "name": "create_settlement_record",
      "description": "Creates a settlement record to track each VisaNet settlement file that is being processed",
      "parameters": {
        "type": "object",
        "properties": {
            "visaNetReportDate": {
              "type": "string",
              "description": "The report date from the VisaNet pdf report, in format yyyy-MM-dd. eg. 2025-04-14",
              "nullable": False
            },
            "visaNetSettlementAmount": {
              "type": "number",
              "description": "The purchase original sale clearing amount from the page with report id VSS-120 and settlement currency TTD in the VisaNet pdf report.",
              "nullable": False
            },
            "visaNetTransactionCount": {
              "type": "number",
              "description": "The purchase original sale count from the page with report id VSS-120 and settlement currency TTD in the VisaNet pdf report.",
              "nullable": False
            },
            "visaNetReportFileName": {
              "type": "string",
              "description": "The file name for the VisaNet report file, with the file extension included. eg. TT Acquirer Visa Files 01.05.2025.pdf",
              "nullable": False
            },
            "emailId": {
              "type": "string",
              "description": "The microsoft graph api email id that this report came from. This value may not always be supplied",
              "nullable": True
            },
            "attachmentId": {
              "type": "string",
              "description": "The microsoft graph api attachment id that this report came from. This value may not always be supplied",
              "nullable": True
            }
        },
        "required": [
          "visaNetReportDate",
          "visaNetSettlementAmount",
          "visaNetTransactionCount",
          "visaNetReportFileName"
        ]
      }
    }
  }

async def create_settlement_record_tool_handler(params_string: str) -> str:
  params_dict: dict = json.loads(params_string)
  create_settlement_dto = CreateSettlementDto(
    visa_net_report_date=params_dict["visaNetReportDate"],
    visa_net_report_fileName=params_dict["visaNetReportFileName"],
    visa_net_settlement_amount=params_dict["visaNetSettlementAmount"],
    visa_net_transaction_count=params_dict["visaNetTransactionCount"],
    email_id= params_dict.get("emailId"),
    attachment_id=params_dict.get("attachmentId")
  )
  try:
    async with get_db_context() as db:
      settlement_service: SettlementService = SettlementService(db)
      await settlement_service.create_settlement(create_settlement_dto)
    return "Settlement created successfully"
  except SettlementAlreadyCompletedError as se:
    logger.info("Settlement Already Completed", exc_info=True)
    return "Settlement Already Completed. No need to continue."
  except Exception as e:
    logger.error(msg=f"Failed to save settlement", exc_info=True)
    return "Failed to create settlement"
