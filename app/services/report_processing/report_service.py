import asyncio
from playwright.async_api import async_playwright
from os import path, makedirs
import logging
import pandas as pd
from pathlib import Path
from urllib.parse import urljoin, quote
from app.settings import APP_ROOT, settings

logger = logging.getLogger(__name__)

class ReportService:
  def __init__(self):
    pass

  def get_visa_net_file_path(self, file_name: str) -> str:
    return path.join(APP_ROOT, "static", "VisaNetFiles", file_name)

  def get_base_report_folder(self) -> str:
    return path.join("static", "FACReports")

  def get_full_report_folder(self) -> str:
    static_folder = path.join(APP_ROOT, "static")
    report_folder =  path.join(static_folder, "FACReports")
    makedirs(report_folder, exist_ok=True)

    return report_folder

  def is_existing_report(self, file_name: str) -> bool:
    full_path = self.get_full_report_path(file_name)
    return path.exists(full_path)


  def get_full_report_path(self, file_name: str) -> str:
    return path.join(self.get_full_report_folder(), file_name)


  def get_url_path(self, file_name: str) -> str:
    file_path = path.join(self.get_base_report_folder(), file_name)
    app_domain = settings.APP_HOST_URL
    if app_domain:
      return urljoin(app_domain, quote(Path(file_path).as_posix()))
    return file_path

  async def generate_excel_report(self, create_report_dto: dict) -> str | None:
    '''
    Start Date in format MM/dd/yyyy. eg. 04/14/2025
    Start Time in format hh:mm tt. eg. 06:00 AM
    End Date in format MM/dd/yyyy. eg. 04/15/2025
    End Time in format hh:mm tt. eg. 05:59 AM
    '''

    attempts = 0
    max_attempts = 3

    fac_settings = {
      "base_url":  settings.FAC_BASE_URL,
      "username":  settings.FAC_USERNAME,
      "password":  settings.FAC_PASSWORD,
      "merchant_legal_name":  settings.FAC_MERCHANT_LEGAL_NAME
    }

    report_start_date = create_report_dto["fac_start_date"]
    report_end_date = create_report_dto["fac_end_date"]

    logger.info(f"Start date {report_start_date} End Date {report_end_date}")

    while attempts < max_attempts:
      attempts += 1

      logger.info(f"Generating report. Attempt {attempts}")

      try:
        async with async_playwright() as p:
          browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"], slow_mo=500)
          context = await browser.new_context()
          page = await context.new_page()

          await page.goto(fac_settings["base_url"])
          await page.fill("#txtUID", fac_settings["username"])
          await page.fill("#txtPwd", fac_settings["password"])
          await page.get_by_role("button", name="Login").click()

          logger.info(f"Logging in. Attempt {attempts}")

          await page.wait_for_url("**/main.htm")

          logger.info(f"Logged in. Attempt {attempts}")
          main_frame = page.frame(name="main")

          await main_frame.get_by_role("cell", name="Transaction (for export to Excel)", exact=True).click()
          await main_frame.get_by_role("cell", name=fac_settings["merchant_legal_name"], exact=True).click()

          await main_frame.locator("#TransactionFilters_dpTStart_dateInput").fill(report_start_date)
          await main_frame.locator("#TransactionFilters_txtStartTime_dateInput").fill("06:00 AM")
          await main_frame.locator("#TransactionFilters_dpTEnd_dateInput").fill(report_end_date)
          await main_frame.locator("#TransactionFilters_txtEndTime_dateInput").fill("05:59 AM")

          await main_frame.locator("#TransactionFilters_cboTransType_Arrow").click()
          await main_frame.get_by_text("Auth", exact=True).click()

          await main_frame.locator("#TransactionFilters_cboStatus_Arrow").click()
          await main_frame.get_by_text("Approved", exact=True).click()

          await main_frame.get_by_role("textbox", name="Numeric currency code").fill("780")
          await main_frame.get_by_role("button", name="View Report").click()

          logger.info(f"Generating report. Attempt {attempts}")
          await page.wait_for_load_state("domcontentloaded")

          await main_frame.locator("#VisibleReportContentReportViewer1_ctl09").wait_for(timeout=30000)

          await main_frame.locator("#ReportViewer1_ctl05_ctl04_ctl00_ButtonLink").click()

          logger.info(f"Downloading report. Attempt {attempts}")
          async with page.expect_download() as download_info:
            await main_frame.get_by_text("Excel", exact=True).click()

          download = await download_info.value

          suggested_filename = download.suggested_filename
          file_name = create_report_dto.get("report_file_name") or suggested_filename
          file_path = self.get_full_report_path(f"{file_name}.xlsx")

          await download.save_as(file_path)

          logger.info(f"Report saved to {file_path}. Attempt {attempts}")
          await browser.close()
          return str(file_path)

      except Exception as error:
        logger.error(msg=f"Failed to generate report. Attempt {attempts}", exc_info=True)
        await asyncio.sleep(5)

    return None

  def extract_csv_from_report(self, excel_file_path: str) -> str:
    file_name = Path(excel_file_path).stem

    df = pd.read_excel(excel_file_path, engine="openpyxl", header=5)

    selected = df[["Date Time", "Order ID", "Amount", "Ccy"]]

    csv_file_path = self.get_full_report_path(f"{file_name}.csv")

    selected.to_csv(csv_file_path, index=False)

    return csv_file_path

  async def generate_csv_report(self, create_report_dto: dict) -> str:
    logger.info(f"Generate report params {create_report_dto}")

    if self.is_existing_report(f"{create_report_dto.get("report_file_name")}.csv"):
      return self.get_full_report_path(f"{create_report_dto.get("report_file_name")}.csv")

    excel_file_path = await self.generate_excel_report(create_report_dto=create_report_dto)

    if not excel_file_path:
      raise ValueError("Failed to generate FAC report")
    return self.extract_csv_from_report(excel_file_path=excel_file_path)