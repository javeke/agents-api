from app.dtos.ai.responses.visa_net_file_check_result import VisaNetFileCheckResult
from app.dtos.events.settlement_event import SettlementEvent
from app.dependencies import get_mail_client
from app.dtos.mail.mail_message_dto import MailAttachmentDto
from app.services.ai import openai_service
import logging 

_logger = logging.getLogger(__name__)


async def process_settlement_automation(event: SettlementEvent):
  mail_client = get_mail_client()
  attachment_dto: MailAttachmentDto | None = await mail_client.get_attachment_by_id(event.attachment_id)

  if not attachment_dto:
    return

  base64_string = attachment_dto.content_bytes.decode("utf-8")
  file_data = f"data:{attachment_dto.content_type};base64,{base64_string}"

  check_result:VisaNetFileCheckResult = openai_service.isVisaNetSettlementFile(file_data=file_data, filename=attachment_dto.name)

  if not check_result.is_visa_net_file:
    _logger.info("File was not seen as ucl plater")
    return
  
  # TODO: Continue from here
