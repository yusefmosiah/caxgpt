import uuid
from typing import List, Optional
from ._sqlalchemy_models import MESSAGE
from .qdrant_client import QdrantClient
from .openai_client import OpenAIClient
from ..models._message import Message, Curation
from sqlalchemy.orm import Session


class MessageNotFoundException(Exception):
    """Exception raised when a message is not found in the database."""


class MessageCreationException(Exception):
    """Exception raised when there is an error creating a message."""


class MessageDeletionException(Exception):
    """Exception raised when there is an error deleting a message."""


class ThoughtSpaceData:
    def __init__(self, qdrant_client: QdrantClient, openai_client: OpenAIClient, db: Session):
        self.qdrant_client = qdrant_client
        self.openai_client = openai_client
        self.db = db

    async def embed_text(self, input_text: str) -> Optional[List[float]]:
        """
        Uses the OpenAI client to embed the input text.
        """
        return await self.openai_client.embed(input_text)

    async def search_similar_messages(
        self, embedding: List[float], search_limit: int = 200, with_vectors: bool = False
    ):
        """
        Uses the Qdrant client to search for similar messages based on the embedding.
        """
        return await self.qdrant_client.search(embedding, search_limit, with_vectors)

    async def retrieve_messages(self, ids: List[str]):
        """
        Retrieves messages by their IDs using the Qdrant client.
        """
        return await self.qdrant_client.retrieve(ids)

    async def upsert_message(self, id: str, input_string: str, embedding: List[float]):
        """
        Upserts a message into the Qdrant collection.
        """
        return await self.qdrant_client.upsert(id, input_string, embedding)

    async def create_message(self, user_id: str, message_id: str):
        try:
            new_message = MESSAGE(user_id=user_id, id=message_id)
            self.db.add(new_message)
            await self.db.commit()
        except Exception as e:
            raise MessageCreationException(f"Failed to create message: {e}")

    async def get_message(self, message_id: str):
        message = await self.db.query(MESSAGE).filter(MESSAGE.id == message_id).first()
        if not message:
            raise MessageNotFoundException(f"Message with ID {message_id} not found")
        return message

    async def get_messages_by_user_id(self, user_id: str):
        try:
            return await self.db.query(MESSAGE).filter(MESSAGE.user_id == user_id).all()
        except Exception as e:
            raise Exception(f"Failed to retrieve messages for user {user_id}: {e}")

    async def delete_message(self, message_id: str):
        try:
            message_to_delete = await self.db.query(MESSAGE).filter(MESSAGE.id == message_id).first()
            if not message_to_delete:
                raise MessageNotFoundException(f"Message with ID {message_id} not found")
            await self.db.delete(message_to_delete)
            await self.db.commit()
        except MessageNotFoundException as e:
            raise e
        except Exception as e:
            raise MessageDeletionException(f"Failed to delete message: {e}")
