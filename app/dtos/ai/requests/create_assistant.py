from typing import Optional
from pydantic import BaseModel

from app.enums.assistant_type import AssistantType
from app.models.assistant import AssistantModel

class CreateAssistantDto(BaseModel):
  name: str
  description: str
  type: AssistantType
  model: Optional[str] = None

  def to_dict(self):
    return {
      "name": self.name,
      "description": self.description,
      "type": self.type,
      "model": self.model
    }