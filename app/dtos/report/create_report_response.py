from pydantic import BaseModel


class CreateReportResponse(BaseModel):
  file_path: str

  def to_dict(self):
    return {
      "file_path": self.file_path
    }