import base64
from typing import List
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from app.dtos.mail.mail_message_dto import MailAttachmentDto, MailEmailAddressDto, MailMessageDto, MailRecipientDto
from app.utils.template_renderer import render_template
from msgraph.generated.users.item.send_mail.send_mail_post_request_body import SendMailPostRequestBody
from msgraph.generated.models.message import Message
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.models.email_address import EmailAddress
from msgraph.generated.models.attachment import Attachment
from msgraph.generated.models.file_attachment import FileAttachment
from msgraph.generated.models.subscription import Subscription
from app.settings import settings
from datetime import datetime, timezone, timedelta
import logging

_logger = logging.getLogger(__name__)

class MailService:
  def __init__(self):
    self._credential: ClientSecretCredential | None = None
    self._client: GraphServiceClient | None = None
    self._service_user: str | None = None

    self._credential = ClientSecretCredential(
      tenant_id= settings.MAIL_CLIENT_TENANT_ID,
      client_id= settings.MAIL_CLIENT_ID,
      client_secret= settings.MAIL_CLIENT_SECRET
    )
    scopes = ['https://graph.microsoft.com/.default']

    self._service_user =  settings.MAIL_SERVICE_USER

    self._client = GraphServiceClient(credentials=self._credential, scopes=scopes)


  async def send_mail(self, subject:str | None = None, html_body: str | None = None, recipients: List[str] = []):
    request_body = SendMailPostRequestBody(
      message = Message(
        subject = subject,
        body = ItemBody(
          content_type = BodyType.Html,
          content = html_body,
        ),
        to_recipients = [
          Recipient(
            email_address = EmailAddress(address = x)
          )
          for x in recipients
        ],
        attachments = [
          FileAttachment(
            odata_type = "#microsoft.graph.fileAttachment",
            name = "attachment.txt",
            content_type = "text/plain",
            content_bytes = base64.urlsafe_b64decode("SGVsbG8gV29ybGQh"),
          ),
        ],
      ),
      save_to_sent_items=True
    )

    await self._client.users.by_user_id(self._service_user).send_mail.post(request_body)


  async def send_settlement_process_mail(self):
    html_body = render_template(
      "email/settlement_process_email.html", {
        "receiver_name": "Aldwyn",
        "visa_net_report_date": "05 May 2025",
        "fac_report_date": "03 May 2025",
        "contact_email": "support@example.com"
      })

    await self.send_mail(subject="Settlement email", html_body=html_body, recipients=["javierbryan11@gmail.com"])

  async def send_settlement_reply_mail(self):
    html_body = render_template(
      "email/settlement_reply_email.html", {
        "receiver_name": "Chris",
        "settlement_account_name": "Wipay JMMB Account",
        "settlement_account_currency_code": "TTD",
        "settlement_account_number": "012345678",
        "visa_net_report_date": "05 May 2025",
        "settlement_total": "12,345.67",
        "fac_report_file_name": "FAC_Report_2025-05-03.csv",
        "contact_email": "support@example.com",
      }
    )

    await self.send_mail(subject="Re: Settlement email", html_body=html_body, recipients=["javierbryan11@gmail.com"])


  async def get_mail_by_id(self, email_id: str) -> MailMessageDto | None:
    message_item = await self._client.users.by_user_id(self._service_user).messages.by_message_id(email_id).get(
      request_configuration={
        "config":{
          "query_parameters":{
            "expand":["attachments"]
          }
        }
      }
    )

    if not message_item:
      return None
    
    mail_message = MailMessageDto(
      id=message_item.id,
      body_preview=message_item.body_preview,
      subject=message_item.subject,
      has_attachment=message_item.has_attachments
    )

    if message_item.from_ and message_item.from_.email_address and message_item.from_.email_address.address:
      mail_message.from_ = MailRecipientDto(
        email_address=MailEmailAddressDto(
          name=message_item.from_.email_address.name,
          address=mail_message.from_.email_address.address
        )
      )

    if message_item.to_recipients and len(message_item.to_recipients) > 0:
      mail_message.to_recipients = []
      for recipient in message_item.to_recipients:
        if recipient.email_address and recipient.email_address.address:
          dto = MailRecipientDto(email_address=MailEmailAddressDto(address=recipient.email_address.address))
          mail_message.to_recipients.append(dto)

    if message_item.bcc_recipients and len(message_item.bcc_recipients) > 0:
      mail_message.bcc_recipients = []
      for recipient in message_item.bcc_recipients:
        if recipient.email_address and recipient.email_address.address:
          dto = MailRecipientDto(email_address=MailEmailAddressDto(address=recipient.email_address.address))
          mail_message.bcc_recipients.append(dto)

    if message_item.cc_recipients and len(message_item.cc_recipients) > 0:
      mail_message.cc_recipients = []
      for recipient in message_item.cc_recipients:
        if recipient.email_address and recipient.email_address.address:
          dto = MailRecipientDto(email_address=MailEmailAddressDto(address=recipient.email_address.address))
          mail_message.cc_recipients.append(dto)

    if message_item.attachments and len(message_item.attachments) > 0:
      mail_message.attachments = []

      for attachment in message_item.attachments:
        if attachment.id:
          dto = MailAttachmentDto(
            odata_type=attachment.odata_type,
            id=attachment.id, content_type=attachment.content_type,
            name=attachment.name, size=attachment.size
          )

          if isinstance(attachment, FileAttachment):
            dto.content_bytes = attachment.content_bytes
          mail_message.attachments.append(dto)

    return 
  
  async def get_attachment_by_id(self, email_id:str, attachment_id: str) -> MailAttachmentDto | None:
    attachment = await self._client.users.by_user_id(self._service_user).messages.by_message_id(
      email_id).attachments.by_attachment_id(attachment_id).get()
    _logger.info(f"Get file {attachment.id} {attachment.content_type}")
    dto = MailAttachmentDto(
      odata_type=attachment.odata_type,
      id=attachment.id, content_type=attachment.content_type,
      name=attachment.name, size=attachment.size
    )

    if isinstance(attachment, FileAttachment):
      dto.content_bytes = attachment.content_bytes

    return dto

  async def create_subscription(self):
    expiration = datetime.now(timezone.utc) + timedelta(minutes=600)

    subscription: Subscription = Subscription(
      change_type="created",
      resource=f"users/{settings.MAIL_SERVICE_USER}/mailFolders('inbox')/messages",
      expiration_date_time=expiration,
      client_state="wipay_automation_api",
      notification_url=f"{settings.APP_HOST_URL}/notification/event"
    )
    await self._client.subscriptions.post(subscription)

