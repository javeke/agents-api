from typing import List, Optional
from pydantic import BaseModel


class MailEmailAddressDto(BaseModel):
  name: str | None
  address: str | None

class MailRecipientDto(BaseModel):
  email_address: MailEmailAddressDto | None


class MailAttachmentDto(BaseModel):
  id: str
  odata_type: str | None
  content_type: Optional[str] = None
  name: Optional[str] = None
  size: Optional[int] = None

  # The base64-encoded contents of the file.
  content_bytes: bytes | None


class MailMessageDto(BaseModel):
  id: str
  body_preview: str | None
  subject: str | None
  has_attachment: bool | None
  sender: MailRecipientDto | None
  bcc_recipients: List[MailRecipientDto] | None
  cc_recipients: List[MailRecipientDto] | None
  to_recipients: List[MailRecipientDto] | None
  from_: MailRecipientDto | None
  attachments: List[MailAttachmentDto] | None

