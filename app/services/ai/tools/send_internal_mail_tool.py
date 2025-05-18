def send_internal_mail_tool_definition() -> dict:
  return {
    "type": "function",
    "function": {
      "name": "send_internal_mail",
      "description": "Sends an email to internal stakeholders to inform of settlement",
      "parameters": {
        "type": "object",
        "properties": {
          "visaNetReportDate": {
            "type": "string",
            "description": "The report date from the VisaNet pdf report, in format yyyy-MM-dd. eg. 2025-04-14",
            "nullable": False
          },
        },
        "required": [
          "visaNetReportDate"
        ]
      }
    }
  }

def send_internal_mail_tool_handler(paramsJson: str) -> str:
  return "Email sent"