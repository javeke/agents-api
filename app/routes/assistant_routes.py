from typing import List, Optional

from fastapi.responses import StreamingResponse

from app.dtos.ai.assistant_dto import AssistantDto
from app.dtos.ai.requests.create_assistant import CreateAssistantDto
from app.dtos.ai.requests.update_assistant import UpdateAssistantRequest
from app.enums.assistant_type import AssistantType
from app.models.assistant import AssistantModel
from app.services.ai import openai_service
from pydantic import ValidationError

from app.services.ai.instructions.accounting_instruction import ACCOUNTING_ASSISTANT_INSTRUCTION
from app.services.report_processing.report_service import ReportService
from app.dependencies import get_report_service

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.dependencies import get_db
import shutil

assistant_router = APIRouter(prefix="/assistant", tags=["assistant"])

@assistant_router.get('/')
async def index(db: AsyncSession = Depends(get_db)):
  query = await db.execute(select(AssistantModel))

  assistants = query.scalars().all()
  
  results = []
  for a in assistants:
    results.append(AssistantDto.from_model(a))

  return results


@assistant_router.get('/{key}')
async def get_assistant_by_id(key: int, db: AsyncSession = Depends(get_db)):
  assistant_model : AssistantModel | None = await db.get(AssistantModel, key)

  if not assistant_model:
    return HTTPException(status_code=404, detail={'errors': [f"Assistant with id {key} not found"]})
  
  assistant = AssistantDto.from_model(assistant_model)

  return assistant

@assistant_router.post('/')
async def create_assistant(assistant: CreateAssistantDto, db: AsyncSession = Depends(get_db)):
  try:
    created_assistant = openai_service.create_assistant(assistant=assistant)

    assistant_model = AssistantModel(
      name=created_assistant.name, description=created_assistant.description, 
      instructions=created_assistant.instructions, type=assistant.type,
      external_id=created_assistant.external_id,model=created_assistant.model
    )

    db.add(assistant_model)
    await db.commit()
    await db.refresh(assistant_model)

    assistant = AssistantDto(
      id=assistant_model.id, name=assistant_model.name, 
      description=assistant_model.description, 
      instructions=assistant_model.instructions, type=assistant.type,
      external_id=assistant_model.external_id,
      model=assistant_model.model, thread_id=assistant_model.thread_id
    )

    return assistant

  except ValidationError as e:
    return {'errors': e.errors()}
  
@assistant_router.put('/{key}')
async def update_assistant(key: int, update_request: UpdateAssistantRequest, db: AsyncSession = Depends(get_db)):
  assistant_model : Optional[AssistantModel] = await db.get(AssistantModel, key)

  if not assistant_model:
    return {'errors': [f"Assistant with id {key} not found"]}

  assistant_model.name = update_request.name or assistant_model.name
  assistant_model.description = update_request.description or assistant_model.description
  assistant_model.instructions = update_request.instructions or assistant_model.instructions
  assistant_model.model = update_request.model or assistant_model.model

  await db.commit()

  assistant = AssistantDto.from_model(assistant_model)

  return assistant

@assistant_router.delete('/{key}')
async def delete_assistant(key: int, db: AsyncSession = Depends(get_db)):
  assistant_model : Optional[AssistantModel] = await db.get(AssistantModel, key)

  if not assistant_model:
    return HTTPException(status_code=404, detail={'errors': [f"Assistant with id {key} not found"]})
  
  if not assistant_model.external_id:
    return HTTPException(status_code=400, detail={'errors': [f"Invalid entity"]})

  is_deleted = openai_service.delete_assistant(assistant_model.external_id)

  if not is_deleted:
    return HTTPException(status_code=500, detail={'errors': [f"Failed to delete assistant"]})
  
  await db.delete(assistant_model)
  await db.commit()

  assistant = AssistantDto.from_model(assistant_model)

  return assistant

@assistant_router.put('/{key}/update-tools')
async def update_assistant_tools(key: int, db: AsyncSession = Depends(get_db)):
  assistant_model: Optional[AssistantModel] = await db.get(AssistantModel, key)
  
  if not assistant_model:
    return HTTPException(status_code=404, detail={'errors':["Invalid assistant"]})
  
  openai_service.update_assistant_tools(assistant_model.external_id)
  return {"result":"success"}

@assistant_router.get('/{key}/thread')
async def get_assistant_messages(key: int, db: AsyncSession = Depends(get_db)):
  assistant_model : Optional[AssistantModel] = await db.get(AssistantModel, key)

  if not assistant_model:
    return HTTPException(status_code=404, detail={'errors': [f"Assistant with id {key} not found"]})
  
  if not assistant_model.external_id:
    return HTTPException(status_code=400, detail={'errors': [f"Invalid entity"]})
  
  if not assistant_model.thread_id:
    return HTTPException(status_code=500, detail={'errors': [f"Invalid entity"]})
  
  messages = openai_service.get_messsages(assistant_model.thread_id)

  return {"messages": messages}

@assistant_router.post('/{key}/stream')
async def create_and_run_thread_message(
  key: int, message: str = Form(),
  uploaded_files: Optional[List[UploadFile]] = File(None, alias="files"),
  db: AsyncSession = Depends(get_db),
  report_service: ReportService = Depends(get_report_service)
):

  assistant_model: Optional[AssistantModel] = await db.get(AssistantModel, key)
  
  if not assistant_model:
    return {'errors':["Invalid assistant"]}
  
  if assistant_model.thread_id == None:
    thread_id: str = openai_service.create_thread()

    assistant_model.thread_id = thread_id
    await db.commit()
    await db.refresh(assistant_model)


  if not message and (not uploaded_files or len(uploaded_files) == 0):
    return {"errors":["A message is required"]}
  
  if uploaded_files:
    for f in uploaded_files:

      normalized_filename = f.filename.replace(" ", "_")

      file_path = report_service.get_visa_net_file_path(normalized_filename)
      with open(file_path, "wb") as buffer:
        shutil.copyfileobj(f.file, buffer)
      f.file.seek(0)
      f.filename = normalized_filename

  newMessageId: str = await openai_service.create_message(assistant_model.thread_id, message=message, files=uploaded_files)
  
  stream = openai_service.run_thread(thread_id=assistant_model.thread_id, assistant_id=assistant_model.external_id)

  return StreamingResponse(stream, media_type="text/event-stream")




  