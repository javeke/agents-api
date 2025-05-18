from pydantic import BaseModel, Field
from typing import List, Optional


class ResourceData(BaseModel):
    '''
    id will be the email id of the new email received
    '''
    id: str 
    odata_type: Optional[str] = Field(alias="@odata.type", default=None)
    odata_id: Optional[str] = Field(alias="@odata.id", default=None)

class NotificationValue(BaseModel):
    subscriptionId: str
    changeType: str
    resource: str
    resourceData: ResourceData
    clientState: Optional[str] = None
    tenantId: Optional[str] = None
    id: Optional[str] = None
    eventType: Optional[str] = None

class NotificationDto(BaseModel):
    value: List[NotificationValue]
