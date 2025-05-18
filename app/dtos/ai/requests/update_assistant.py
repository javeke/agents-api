from typing import Optional
from pydantic import BaseModel

class UpdateAssistantRequest(BaseModel):
  name: Optional[str] = None
  description: Optional[str] = None
  instructions: Optional[str] = None
  model: Optional[str] = None