import json

from fastapi import Depends

from app.dependencies import get_report_service
from app.dtos.report.create_report_dto import CreateReportDto
from app.services.report_processing.report_service import ReportService

def generate_fac_report_tool_definition() -> dict:
  return {
    "type":"function",
    "function":{
      "name":"generate_fac_report",
      "description":"Generates a FAC transaction report for the specified period and returns an open ai file_id, the file name and file type. This period must be within 1 year of the current date.",
      "parameters":{
        "type":"object",
        "properties": {
          "facReportStartDate": {
            "type": "string",
            "description": "The start date for the FAC report in format MM/dd/yyyy. Typically, 2 days before the corresponding Visa Net report date",
            "nullable": False
          },
          "facReportEndDate": {
            "type": "string",
            "description": "The end date for the FAC report in format MM/dd/yyyy. Typically, 1 day after the fac report start date except for when the fac report start date is a Friday in which case the fac report end date would be 3 days after the fac report start date",
            "nullable": False
          },
          "reportFileName": {
            "type": "string",
            "description": "The name of the csv file to be generated without the file extension. eg. fac_report_05_01_2024",
            "nullable": False
          }
        }
      }
    }
  }

async def generate_fac_report_tool_handler(params_json: str) -> str:
  params_dict = json.loads(params_json)
  create_report_dto = CreateReportDto(
    fac_start_date=params_dict["facReportStartDate"],
    fac_end_date=params_dict["facReportEndDate"],
    report_file_name=params_dict["reportFileName"]
  )
  report_service: ReportService = get_report_service()
  file_path = await report_service.generate_csv_report(create_report_dto=create_report_dto.to_dict())

  return file_path