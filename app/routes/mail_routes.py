from fastapi import APIRouter, Depends

from app.dependencies import get_mail_client
from app.services.mail.mail_service import MailService

mail_router = APIRouter(prefix="/mail", tags=["mail"])

@mail_router.post('/')
async def send_test_mail(mail_client: MailService = Depends(get_mail_client)):
  await mail_client.send_mail(subject="Test mail from python", html_body="Some html", recipients=["javierbryan11@gmail.com"])
  return "mail sent"

@mail_router.post('/send-settlement-reply-mail')
async def send_settlement_reply_mail(mail_client: MailService = Depends(get_mail_client)):
  await mail_client.send_settlement_reply_mail()
  return "Mail send"


@mail_router.post('/send-settlement-process-mail')
async def send_settlement_process_mail(mail_client: MailService = Depends(get_mail_client)):
  await mail_client.send_settlement_process_mail()
  return "Mail sent"