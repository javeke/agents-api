from typing import Optional
from sqlalchemy import Enum as SQLAEnum, Column, Integer, String, Text
from ..enums.assistant_type import AssistantType
from ..db import Base

class AssistantModel(Base):
  __tablename__ = "assistant"
  id: int = Column(Integer, primary_key=True)
  name: str = Column(String(100))
  description: str = Column(Text)
  instructions: str = Column(Text)
  thread_id: Optional[str] = Column(String(255), nullable=True)
  external_id: Optional[str] = Column(String(255), nullable=True)
  type: AssistantType = Column(SQLAEnum(AssistantType), nullable=False)
  model: Optional[str] = Column(String(100), nullable=True)