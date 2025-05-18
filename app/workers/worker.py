from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

from app.dtos.events.settlement_event import SettlementEvent
from app.services.automation.settlement_automation import process_settlement_automation
from ..settings import settings
from app.workers.shared_queue import email_event_queue, settlement_event_queue
from app.services.mail.mail_service import MailService
from app.services.ai import openai_service
from app.dependencies import get_mail_client
_logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def renew_subscription():
  _logger.info("Renewing subscription")
  _logger.info(f"{settings.APP_HOST_URL} Debug {settings.DEBUG}")


async def process_email_event():
  email_id = await email_event_queue.get()
  mail_service: MailService = get_mail_client()

  mail_message = await mail_service.get_mail_by_id(email_id=email_id)

  if mail_message and mail_message.has_attachment and mail_message.attachments:
    for attachment in mail_message.attachments:
      if attachment.name:
        visa_filename_check = openai_service.isVisaNetSettlementFileName(attachment.name)

        if visa_filename_check:
          await settlement_event_queue.put(SettlementEvent(email_id=mail_message.id, attachment_id=attachment.id))


async def process_settlement_event():
  settlement_event = await settlement_event_queue.get()

  await process_settlement_automation(settlement_event)