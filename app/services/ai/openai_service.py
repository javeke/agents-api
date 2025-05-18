import io
import json
from pathlib import Path
from typing import List, Text, override
from openai import OpenAI, AssistantEventHandler
from openai.types import beta
from openai.types.beta import AssistantToolParam, CodeInterpreterToolParam, FileSearchToolParam
from openai.types.beta.thread import ToolResources, ToolResourcesFileSearch, ToolResourcesCodeInterpreter
from openai.types.beta.threads import TextDelta
from openai.types.beta.threads.run import Run

from app.dtos.ai.requests.create_assistant import CreateAssistantDto
from app.dtos.ai.responses.visa_net_file_check_result import VisaNetFileCheckResult, VisaNetFileNameCheckResult
from app.enums.assistant_type import AssistantType
from app.services.ai.instructions.accounting_instruction import ACCOUNTING_ASSISTANT_INSTRUCTION
from app.services.ai.tools.create_settlement_tool import create_settlement_record_tool_definition, create_settlement_record_tool_handler
from app.services.ai.tools.extract_visanet_tool import extract_visa_net_data, extract_visa_net_data_tool_definition
from app.services.ai.tools.generate_fac_report_tool import generate_fac_report_tool_definition, generate_fac_report_tool_handler
from app.services.ai.tools.send_internal_mail_tool import send_internal_mail_tool_definition, send_internal_mail_tool_handler
from app.services.ai.tools.send_reply_mail_tool import send_reply_mail_tool_definition, send_reply_mail_tool_handler
from app.services.ai.tools.update_settlement_tool import update_settlement_record_tool_definition, update_settlement_record_tool_handler
from ...dtos.ai.assistant_dto import AssistantDto
from fastapi import UploadFile
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

client = OpenAI()

class StreamEventHandler(AssistantEventHandler):
  def __init__(self):
    super().__init__()
    self.buffer: List[str] = []

  @override
  def on_text_delta(self, delta : TextDelta, snapshot: Text):
    self.buffer.append(delta.value)
  
  def stream_data(self):
    for chunk in self.buffer:
      yield chunk.encode(encoding="utf-8")


def get_assistants() -> list[AssistantDto]:
  assistants = client.beta.assistants.list()

  result = []
  for assistant in assistants.data:
    result.append(AssistantDto(id=assistant.id, name=assistant.name, description=assistant.description, instructions=assistant.instructions))

  return result

def create_assistant(assistant: CreateAssistantDto) -> AssistantDto:

  tools: List[AssistantToolParam] = []

  accounting_tools = [create_settlement_record_tool_definition(), generate_fac_report_tool_definition(),
    update_settlement_record_tool_definition(), send_reply_mail_tool_definition(),
    send_internal_mail_tool_definition(), extract_visa_net_data_tool_definition()
  ]
  instructions: str | None = None
  if assistant.type == AssistantType.ACCOUNTING:
    tools.extend(accounting_tools)
    instructions = ACCOUNTING_ASSISTANT_INSTRUCTION
  else:
    raise ValueError("Unsupported assistant type")
  
  new_assistant = client.beta.assistants.create(
    model="gpt-4o-2024-11-20", description=assistant.description, 
    instructions=instructions, name=assistant.name,
    temperature=0.01, reasoning_effort="high",
    tools=[{"type": "file_search"}, {"type": "code_interpreter"}, *tools]
  )

  result = AssistantDto(
    name=new_assistant.name, description=new_assistant.description, 
    instructions=new_assistant.instructions, type=assistant.type,
    external_id=new_assistant.id,model=new_assistant.model
  )

  return result

def update_assistant_tools(assistant_id: str):
  assistant_returned = client.beta.assistants.retrieve(assistant_id=assistant_id)

  existing_tools = assistant_returned.tools

  existing_function_name_set = {x.function.name for x in existing_tools if x.type == "function"}

  available_tools = {
    "create_settlement_record": create_settlement_record_tool_definition(),
    "update_settlement_record": update_settlement_record_tool_definition(),
    "generate_fac_report": generate_fac_report_tool_definition(),
    "send_reply_mail": send_reply_mail_tool_definition(),
    "send_internal_mail": send_internal_mail_tool_definition()
  }

  for func_name, func_def in available_tools.items():
    if func_name in existing_function_name_set:
      continue
    existing_tools.append(func_def)
    existing_function_name_set.add(func_name)


  client.beta.assistants.update(assistant_id=assistant_id, tools=existing_tools)


def delete_assistant(assistant_id: str) -> bool:
  assistant_deleted = client.beta.assistants.delete(assistant_id=assistant_id)

  return assistant_deleted.deleted

def create_thread() -> str:
  thread: beta.thread.Thread = client.beta.threads.create()
  return thread.id

async def create_message(thread_id:str, message: str | None, files: List[UploadFile] | None) -> str:
  stored_thread = client.beta.threads.retrieve(thread_id)

  if not stored_thread:
    raise ValueError("Thread does not exist")

  tool_resources = stored_thread.tool_resources or ToolResources()
  code_interpreter_resources : ToolResourcesCodeInterpreter = tool_resources.code_interpreter or ToolResourcesCodeInterpreter()
  file_search_resources: ToolResourcesFileSearch = tool_resources.file_search or ToolResourcesFileSearch()

  vector_store_id: str | None = None

  file_ids: List[str] = []

  if files and len(files) > 0:
    for f in files:
      file_stream = io.BytesIO(await f.read())
      file_stream.name = f.filename
      res = client.files.create(purpose="assistants", file=file_stream)
      file_ids.append(res.id)

  if len(file_ids) > 0:
    code_interpreter_resources.file_ids = code_interpreter_resources.file_ids or []

    for f_id in file_ids:
      if f_id not in code_interpreter_resources.file_ids:
        code_interpreter_resources.file_ids.append(f_id)

    file_search_resources.vector_store_ids = file_search_resources.vector_store_ids or []

    if len(file_search_resources.vector_store_ids) == 0:
      prefix = "thread_vector_store"
      timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
      filename = f"{prefix}_{timestamp}"

      file_search_resources.vector_store_ids.append(client.vector_stores.create(name=f"{filename}").id)
    
    vector_store_id = file_search_resources.vector_store_ids[0]

    client.vector_stores.file_batches.create_and_poll(vector_store_id=vector_store_id, file_ids=file_ids)

    tool_resources.file_search = file_search_resources
    tool_resources.code_interpreter = code_interpreter_resources

    stored_thread = client.beta.threads.update(thread_id=stored_thread.id, tool_resources=tool_resources)


  params = {}

  if message:
    params['content'] = message

  newMessageId = client.beta.threads.messages.create(thread_id, role="user", **params).id

  return newMessageId

  
async def run_thread(thread_id: str, assistant_id: str):
  
  stream_manager = client.beta.threads.runs.stream(
    thread_id=thread_id, assistant_id=assistant_id, 
    parallel_tool_calls=False, response_format={
      "type":"json_schema",
      "json_schema":{
        "name":"reconciliation_outcome",
        "description":"This output respresent the details of a settlement process",
        "schema":{
          "type":"object",
          "properties": {
            "is_settled_success": {
              "type":"boolean",
              "description": "A boolean value indicating whether you were able to successfully reconcile the report or not."
            },
            "discrepancies_found": {
              "type":"array",
              "description":"A array of description of all discrepancies found, if any. Empty array if no discrepancies were found",
              "items":{
                "type":"string",
                "description":"a string describing a descrepancy that was found"
              }
            },
            "discrepancies_resolved": {
              "type":"array",
              "description":"A array of descriptions of the steps taken to resolve a particular descrepancy, if it was resolved",
              "items":{
                "type":"string",
                "description":"a string describing a descrepancy that was resolved"
              }
            },
            "brief_summary":{
              "type":"string",
              "description":"A brief summary or review of the process for this settlement not exceeding 500 words",
            },
            "errors":{
              "type":"array",
              "description":"A list of errors that occurred while attempting to process settlement",
              "items":{
                "type":"string",
                "description":"a brief description of each error"
              }
            }
          },
          "additionalProperties": False,
          "required":["is_settled_success"]
        }
      }
    }
  )
  current_run: Run | None = None 

  try:
    while True:
      tool_outputs = []
      current_run = None
      with stream_manager as stream:
        for event in stream:
          if (
            event.event == "thread.run.completed"
            or event.event == "thread.run.cancelled"
            or event.event == "thread.run.expired"
            or event.event == "thread.run.failed"
            or event.event == "thread.run.incomplete"
            or event.event == "thread.run.created"
            or event.event == "thread.run.in_progress"
            or event.event == "thread.run.cancelling"
            or event.event == "thread.run.queued"
          ):
            logger.info(f"{event.data.id} {event.event}")
            current_run = event.data
            
          elif event.event == "thread.run.requires_action":
            logger.info(f"{event.data.id} {event.event}")
            current_run = event.data
            for tool in current_run.required_action.submit_tool_outputs.tool_calls:
              output = None
              logger.info(f"Function call {tool.function.name} with args {tool.function.arguments}")
              if tool.function.name == "extract_visa_net_data":
                params_dict: dict = json.loads(tool.function.arguments)

                # retrieved_file = client.files.retrieve(Path(params_dict["visaNetReportFileName"]).stem)

                (count, amount, report_date) = extract_visa_net_data(params_dict["visaNetReportFileName"])

                output = json.dumps({
                  "visa_net_file_transaction_count": count,
                  "visa_net_file_transaction_amount": str(amount),
                  "visa_net_file_report_date": report_date.strftime('%Y-%m-%d')
                })
              elif tool.function.name == "create_settlement_record":
                output = await create_settlement_record_tool_handler(tool.function.arguments)
              elif tool.function.name == "update_settlement_record":
                output = await update_settlement_record_tool_handler(tool.function.arguments)
              elif tool.function.name == "generate_fac_report":
                csv_file_path = await generate_fac_report_tool_handler(tool.function.arguments)
                res = client.files.create(purpose="assistants", file=Path(csv_file_path))
                report_file_id = res.id

                stored_thread = client.beta.threads.retrieve(thread_id)

                existing_tool_resources = stored_thread.tool_resources or ToolResources()
                code_interpreter_resources = existing_tool_resources.code_interpreter or ToolResourcesCodeInterpreter()
                code_interpreter_file_ids = code_interpreter_resources.file_ids or []

                code_interpreter_file_ids.append(report_file_id)
                code_interpreter_resources.file_ids = code_interpreter_file_ids
                existing_tool_resources.code_interpreter = code_interpreter_resources

                stored_thread = client.beta.threads.update(thread_id=stored_thread.id, tool_resources=existing_tool_resources)

                output = json.dumps({"open_ai_file_id": report_file_id})
                
              elif tool.function.name == "send_reply_mail":
                output = send_reply_mail_tool_handler(tool.function.arguments)
              elif tool.function.name == "send_internal_mail":
                output = send_internal_mail_tool_handler(tool.function.arguments)
              else:
                raise ValueError(f"Unrecognized function call {tool.function.name}")

              tool_outputs.append({"tool_call_id": tool.id, "output":output})

          elif event.event == "thread.message.delta":
            for content_delta in event.data.delta.content or []:
              if content_delta.type == "text" and content_delta.text and content_delta.text.value:
                yield content_delta.text.value.encode(encoding="utf-8")
      
      if not current_run:
        break
        
      current_run = client.beta.threads.runs.retrieve(run_id=current_run.id, thread_id=thread_id)

      if len(tool_outputs) > 0 and current_run.status == "requires_action" and current_run.required_action.type == "submit_tool_outputs":
        stream_manager = client.beta.threads.runs.submit_tool_outputs_stream(run_id=current_run.id, thread_id=thread_id, tool_outputs=tool_outputs)
      
      logger.info(f"End of loop for run {current_run.id} in state {current_run.status}")
      if not current_run or current_run.status in ["completed", "failed", "cancelled", "expired"]:
        

        break
    
  except Exception as e:
    logger.error(msg=f"Open AI error", exc_info=True)
    if current_run:
      client.beta.threads.runs.cancel(current_run.id, thread_id=thread_id)


def get_messsages(thread_id: str):
  response = client.beta.threads.messages.list(thread_id=thread_id, order='desc', limit=50)

  messages = response.data

  results : List[str] = []

  for message in messages:
    m:str = ""
    for c in message.content:
      if c.type == "text":
        m += c.text.value
    results.append(m)

  return results

def queryWithAI(query: str, file_data: str | None = None, filename: str | None = None) -> str:
  content = []
  if filename and file_data:
    content.append({
      "type":"input_file",
      "filename": filename,
      "file_data":file_data 
    })

  content.append({
    "type":"input_text",
    "text":query
  })

  response = client.responses.create(
    model="gpt-4o-2024-11-20",
    temperature=0.1,
    input=[
      {
        "role":"user",
        "content":content
      }
    ]
  )

  return response.output_text

def isVisaNetSettlementFileName(filename: str) -> bool:
  content = [
    {
      "type":"input_text",
      "text":filename
    }
  ]

  response = client.responses.parse(
    instructions="You are a financial auditor who handles settlements between a Visa and an acquiring bank. VisaNet settlement" \
    "reports are typically pdf files with names like 'TT  Acquirer Visa Files 07.05.2025.pdf' and 'TT Aquirer Visa Files 01.01.2025.pdf'." \
    "You will be provided with a filename, return a True value if the filename provided could possible be one for a VisaNet" \
    "settlement report",
    model="gpt-4o-2024-11-20", temperature=0.1,
    input=[
      {
        "role":"user",
        "content":content
      }
    ],
    text_format=VisaNetFileNameCheckResult
  )

  return response.output_parsed.is_similiar if response.output_parsed else False

def isVisaNetSettlementFile(file_data: str, filename: str) -> VisaNetFileCheckResult:
  content = []
  if filename and file_data:
    content.append({
      "type":"input_file",
      "filename": filename,
      "file_data":file_data 
    })

  response = client.responses.parse(
    instructions="You are a financial auditor who handles settlements between a Visa and an acquiring bank. " \
    "You will be provided with a file, indicate whether the file is a VisaNet Settlement report file or not." \
    "If it is a visa net settlement report then extract the report date in format yyyy-MM-dd. eg. 2025-04-14," \
    " the original sale count and original sale clearing amount for the report with report id VSS 120 and " \
    "settlement currency TTD.",
    model="gpt-4o-2024-11-20",
    temperature=0.1,
    input=[
      {
        "role":"user",
        "content":content
      }
    ],
    text_format=VisaNetFileCheckResult
  )

  return response.output_parsed