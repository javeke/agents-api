from fastapi import APIRouter, Request
from app.workers.shared_queue import email_event_queue
from app.dtos.notifications.notification_dto import NotificationDto
import logging

_logger = logging.getLogger(__name__)

notification_router = APIRouter(prefix="/notification", tags=["notification"])

@notification_router.post("/event")
async def notification_webhook(request: Request):
  if "validationToken" in request.query_params:
        return request.query_params["validationToken"]
  
  body = await request.json()
  dto = NotificationDto.model_validate(body, strict=False)

  if not dto or not dto.value or len(dto.value) == 0:
     return "Recevied"

  for notification in dto.value:
    try:
       if not notification.resourceData or not notification.resourceData.id:
          continue
       if notification.changeType != "created" or notification.clientState != "wipay_automation_api":
          continue
       email_id = notification.resourceData.id
       await email_event_queue.put(email_id)
    except Exception as e:
     _logger.error("Failed to process event", exc_info=True)

  return ""

@notification_router.post("/subscribe")
def create_webhook():
  return ""