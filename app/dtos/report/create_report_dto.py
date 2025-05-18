from typing import Optional
from pydantic import BaseModel


class CreateReportDto(BaseModel):
  fac_start_date: str
  fac_end_date: str
  report_file_name: Optional[str]

  def to_dict(self):
    return {
      "fac_start_date": self.fac_start_date,
      "fac_end_date": self.fac_end_date,
      "report_file_name": self.report_file_name
    }