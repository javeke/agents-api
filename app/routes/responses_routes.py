
import base64
from typing import List, Optional
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from app.services.ai import openai_service
import logging

logger = logging.getLogger(__name__)

responses_router = APIRouter(prefix="/responses", tags=["responses"])

@responses_router.post('/queryAI')
async def queryAI(
  message: str = Form(),
  uploaded_file: Optional[UploadFile] = File(None, alias="file"),
):
  
  kwargs = {}

  if uploaded_file:
    file_bytes = await uploaded_file.read()
    file_type = uploaded_file.content_type
    logger.info(f"{uploaded_file.filename} of type {file_type}")
    base64_string = base64.b64encode(file_bytes).decode("utf-8")
    file_data = f"data:{file_type};base64,{base64_string}"

    kwargs["filename"] = uploaded_file.filename
    kwargs["file_data"] = file_data
      

  return openai_service.queryWithAI(message, **kwargs)

@responses_router.post('/visa-net-file-check')
async def visa_net_file_check(
  uploaded_file: UploadFile = File(None, alias="file"),
):
  if not uploaded_file:
    return HTTPException(status_code=400, detail={'errors': ["file is required"]})
  
  file_bytes = await uploaded_file.read()
  file_type = uploaded_file.content_type
  logger.info(f"{uploaded_file.filename} of type {file_type}")
  base64_string = base64.b64encode(file_bytes).decode("utf-8")
  file_data = f"data:{file_type};base64,{base64_string}"

  return openai_service.isVisaNetSettlementFile(file_data=file_data, filename=uploaded_file.filename)