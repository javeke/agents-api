from fastapi import FastAPI
from contextlib import asynccontextmanager

from .routes.assistant_routes import assistant_router
from .routes.mail_routes import mail_router
from .routes.report_routes import report_router
from .routes.responses_routes import responses_router
from .routes.notification_routes import notification_router
from datetime import datetime
from apscheduler.triggers.interval import IntervalTrigger

import logging
from app.workers.worker import process_email_event, process_settlement_event, scheduler, renew_subscription

logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

async def lifespan(application: FastAPI):
  scheduler.add_job(renew_subscription, IntervalTrigger(minutes=30), id="renew_subscription")
  # TODO: Remember to add these
  # scheduler.add_job(process_email_event, IntervalTrigger(minutes=30), id="process_email_event")
  # scheduler.add_job(process_settlement_event, IntervalTrigger(minutes=30), id="process_settlement_event")
  
  scheduler.start()

  yield

  scheduler.shutdown(wait=True)

app = FastAPI(lifespan=lifespan)

app.include_router(assistant_router)
app.include_router(mail_router)
app.include_router(report_router)
app.include_router(responses_router)
app.include_router(notification_router)


