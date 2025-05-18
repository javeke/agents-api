from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
import logging
from app.dtos.report.create_report_dto import CreateReportDto
from app.dtos.report.create_report_response import CreateReportResponse
from app.dependencies import get_report_service
from app.services.report_processing.report_service import ReportService

report_router = APIRouter(prefix="/report", tags=["report"])

logger = logging.getLogger(__name__)

@report_router.get('/test')
def test(report_service: ReportService = Depends(get_report_service)):
  return report_service.get_url_path(f"some_file.xlsx")

@report_router.post("/generate-excel")
async def generate_report(dto: CreateReportDto, report_service: ReportService = Depends(get_report_service)):
  """
  Generate a FAC report
  """
  result_url = None
  if report_service.is_existing_report(f"{dto.report_file_name}.xlsx"):
    result_url = report_service.get_url_path(f"{dto.report_file_name}.xlsx")
  else:
    abs_url = await report_service.generate_excel_report(dto.to_dict())
    file_name = Path(abs_url).stem
    result_url = report_service.get_url_path(file_name)

  return CreateReportResponse(file_path=result_url)

@report_router.post("/generate-csv")
async def generate_csv_report(dto: CreateReportDto, report_service: ReportService = Depends(get_report_service)):

  result_url = None
  if report_service.is_existing_report(f"{dto.report_file_name}.csv"):
    result_url = report_service.get_url_path(f"{dto.report_file_name}.csv")
  
  elif report_service.is_existing_report(f"{dto.report_file_name}.xlsx"):
    abs_url = report_service.extract_csv_from_report(report_service.get_full_report_path(f"{dto.report_file_name}.xlsx"))
    file_name = Path(abs_url).stem
    result_url = report_service.get_url_path(file_name)
  else:
    abs_url = await report_service.generate_csv_report(dto.to_dict())
    file_name = Path(abs_url).stem
    result_url = report_service.get_url_path(file_name)

  if not result_url:
    return HTTPException(status_code=500, detail={"errors":["Failed to generate report"]})

  return CreateReportResponse(file_path=result_url)