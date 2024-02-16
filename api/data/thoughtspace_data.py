import uuid
import logging
import math
from typing import List, Optional
from ._sqlalchemy_models import MESSAGE, USER
from .qdrant_client import QdrantClient
from .openai_client import OpenAIClient
from ..models._message import Message, Curation
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class MessageNotFoundException(Exception):
    """Exception raised when a message is not found in the database."""


class MessageCreationException(Exception):
    """Exception raised when there is an error creating a message."""


class MessageDeletionException(Exception):
    """Exception raised when there is an error deleting a message."""


class ThoughtSpaceData:
    def __init__(self, db: Session):
        self.qdrant_client = QdrantClient()
        self.openai_client = OpenAIClient()
        self.db = db
        logger.info("ThoughtSpaceData initialized")

    async def embed_text(self, input_text: str) -> Optional[List[float]]:
        logger.info(f"Embedding text: {input_text[:30]}...")
        return await self.openai_client.embed(input_text)

    async def search_similar_messages(
        self, embedding: List[float], search_limit: int = 200, with_vectors: bool = False
    ):
        logger.info(f"Searching for similar messages with search limit {search_limit} and with_vectors={with_vectors}")
        return await self.qdrant_client.search(embedding, search_limit, with_vectors)

    async def retrieve_messages(self, ids: List[str]):
        logger.info(f"Retrieving messages with IDs: {ids}")
        return await self.qdrant_client.retrieve(ids)

    async def upsert_message(self, id: str, input_string: str, embedding: List[float]):
        logger.info(f"Upserting message with ID {id}")
        await self.qdrant_client.upsert(id, input_string, embedding)

    def create_message(self, user_id: str, message_id: str):
        try:
            logger.info(f"Creating message with ID {message_id} for user {user_id}")
            new_message = MESSAGE(user_id=user_id, id=message_id)
            self.db.add(new_message)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to create message: {e}")
            raise MessageCreationException(f"Failed to create message: {e}")

    def get_message(self, message_id: str):
        logger.info(f"Getting message with ID {message_id}")
        message = self.db.query(MESSAGE).filter(MESSAGE.id == message_id).first()
        if not message:
            logger.warning(f"Message with ID {message_id} not found")
            raise MessageNotFoundException(f"Message with ID {message_id} not found")
        return message

    def get_messages_by_user_id(self, user_id: str):
        try:
            logger.info(f"Getting messages for user ID {user_id}")
            return self.db.query(MESSAGE).filter(MESSAGE.user_id == user_id).all()
        except Exception as e:
            logger.error(f"Failed to retrieve messages for user {user_id}: {e}")
            raise Exception(f"Failed to retrieve messages for user {user_id}: {e}")

    def delete_message(self, message_id: str):
        try:
            logger.info(f"Deleting message with ID {message_id}")
            message_to_delete = self.db.query(MESSAGE).filter(MESSAGE.id == message_id).first()
            if not message_to_delete:
                logger.warning(f"Message with ID {message_id} not found for deletion")
                raise MessageNotFoundException(f"Message with ID {message_id} not found")
            self.db.delete(message_to_delete)
            self.db.commit()
        except MessageNotFoundException as e:
            raise e
        except Exception as e:
            logger.error(f"Failed to delete message: {e}")
            raise MessageDeletionException(f"Failed to delete message: {e}")

    def get_user_voice_balance_and_messages(self, user_id: str):
        user = self.db.query(USER).filter(USER.id == user_id).first()
        if not user:
            logger.error(f"User with ID {user_id} not found")
            return None
        messages = self.db.query(MESSAGE.id).filter(MESSAGE.user_id == user_id).all()
        message_ids = [message.id for message in messages]
        return {"voice_balance": user.voice, "message_ids": message_ids}

    def update_user_voice_balance(self, user_id: str, voice_amount: float):
        print("before_query")

        user = self.db.query(USER).filter(USER.id == user_id).first()
        print(f"user: {user}")
        if user:
            # Calculate the floor of the voice_amount and add it to the user's voice score
            voice_to_add = math.floor(voice_amount * 100)
            user.voice += voice_to_add
            self.db.commit()
            logger.info(f"Added {voice_to_add} VOICE to user {user_id}'s balance.")
        else:
            logger.error(f"User with ID {user_id} not found")
