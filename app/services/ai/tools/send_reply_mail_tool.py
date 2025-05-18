def send_reply_mail_tool_definition() -> dict:
  return {
    "type": "function",
    "function": {
      "name": "send_reply_mail",
      "description": "Sends a reply email to acquirer to settlement clearing amount",
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


def send_reply_mail_tool_handler(paramsJson: str) -> str:
  return "Email sent successfully"