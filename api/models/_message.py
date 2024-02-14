from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class Curation(BaseModel):
    user_id: str
    message_id: str
    created_at: datetime

class Message(BaseModel):
    id: UUID
    content: str
    voice: Optional[int] = 0
    curations: Optional[List[Curation]] = []
    created_at: datetime
    updated_at: datetime

class MessagesResponse(BaseModel):
    messages: List[Message]
