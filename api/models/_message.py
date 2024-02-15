from pydantic import BaseModel, Field, validator
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class NewMessageRequest(BaseModel):
    input_text: str


class Curation(BaseModel):
    user_id: str
    message_id: str
    created_at: datetime = Field(default_factory=datetime.now)


class Message(BaseModel):
    id: UUID
    content: str
    voice: Optional[int] = 0
    curations: Optional[List[Curation]] = []
    created_at: datetime = Field(default_factory=datetime.now)

    @validator("voice", pre=True, always=True)
    def convert_voice_to_int(cls, v):
        return int(round(v))


class MessagesResponse(BaseModel):
    messages: List[Message]
