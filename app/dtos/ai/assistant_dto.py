from typing import Optional
from pydantic import BaseModel

from app.enums.assistant_type import AssistantType
from app.models.assistant import AssistantModel

class AssistantDto(BaseModel):
  id: Optional[int] = None
  name: str
  description: str
  instructions: Optional[str] = None
  type: AssistantType
  external_id: Optional[str] = None
  thread_id: Optional[str] = None
  model: Optional[str] = None

  def to_dict(self):
    return {
      "id": self.id,
      "name": self.name,
      "description": self.description,
      "instructions": self.instructions,
      "type": self.type,
      "external_id": self.external_id,
      "thread_id": self.thread_id,
      "model": self.model
    }
  
  def from_model(assistant_model: AssistantModel):
    return AssistantDto(
      id=assistant_model.id, name=assistant_model.name, 
      description=assistant_model.description, 
      instructions=assistant_model.instructions, type=assistant_model.type,
      external_id=assistant_model.external_id,
      model=assistant_model.model, thread_id=assistant_model.thread_id
    )