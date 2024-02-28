from pydantic import BaseModel, Field, validator
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class NewMessageRequest(BaseModel):
    input_text: str


class Revision(BaseModel):
    user_id: str
    message_id: str
    created_at: datetime = Field(default_factory=datetime.now)


class Message(BaseModel):
    id: UUID
    content: str
    similarity_score: float
    reranking_score: Optional[float] = None
    voice: Optional[int] = None  # Change default to None
    revisions_count: Optional[int] = None  # Replace revisions list with count, default to None
    created_at: datetime = Field(default_factory=datetime.now)

    @validator("voice", pre=True, always=True)
    def convert_voice_to_int(cls, v):
        if v is None:
            return None
        try:
            return int(round(v))
        except TypeError:
            raise ValueError("Voice must be a number or None")


class MessagesResponse(BaseModel):
    messages: List[Message]

class RevisionRequest(BaseModel):
    message_id: UUID
    revised_text: str
    voice: int
