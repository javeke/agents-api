import os
from pathlib import Path
from pydantic_settings import BaseSettings

from dotenv import load_dotenv

load_dotenv(override=True)

class Settings(BaseSettings):
  OPENAI_API_KEY: str
  SQLALCHEMY_DATABASE_URI: str
  SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
  DEBUG: bool = True
  # FAC Settings
  FAC_BASE_URL: str = "https://marlin.firstatlanticcommerce.com/sentry/paymentgateway/merchant/administration/WfrmLogin.aspx"
  FAC_MERCHANT_LEGAL_NAME: str = "Wipay JMMB"
  FAC_USERNAME: str
  FAC_PASSWORD: str
  APP_HOST_URL: str
  MAIL_CLIENT_TENANT_ID: str
  MAIL_CLIENT_ID: str
  MAIL_CLIENT_SECRET: str
  MAIL_SERVICE_USER: str

  class Config:
    env_file = ".env"


settings = Settings()

APP_ROOT = Path(__file__).resolve().parent