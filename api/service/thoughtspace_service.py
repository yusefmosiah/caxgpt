from typing import List
from ..data.thoughtspace_data import ThoughtSpaceData
from ..models._message import Message, Curation, MessagesResponse
from datetime import datetime
from qdrant_client.http.models import ScoredPoint
from sqlalchemy.orm import Session
import uuid


class ThoughtSpaceService:
    def __init__(self, db: Session):
        self.thoughtspace_data = ThoughtSpaceData(db=db)

    async def embed_and_search_messages(
        self, input_text: str, search_limit: int = 200, with_vectors: bool = False
    ) -> MessagesResponse:
        """
        Embeds the input text using OpenAI, searches for similar messages using Qdrant, and returns the search results.
        """
        embedding = await self.thoughtspace_data.embed_text(input_text)
        search_results = await self.thoughtspace_data.search_similar_messages(embedding, search_limit, with_vectors)
        messages = [self.scored_point_to_message(result) for result in search_results]
        return MessagesResponse(messages=messages)

    async def deduplicate_messages(self, messages: List[Message]) -> List[Message]:
        print("start dedup")
        print(len(messages))
        # Normalize content by stripping whitespace and converting to lowercase
        normalized_content = lambda message: message.content.strip().lower()
        # Sort messages by created_at timestamp to ensure earlier messages are prioritized
        messages.sort(key=lambda message: message.created_at)
        print("sorted messages")
        print(messages[:10])

        unique_messages_dict = {}
        for message in messages:
            content_key = normalized_content(message)
            if content_key not in unique_messages_dict:
                unique_messages_dict[content_key] = message

        unique_messages = list(unique_messages_dict.values())
        print(f"unique count: {len(unique_messages)}")
        return unique_messages
    # Additional methods for curating messages, etc., can be added here

    def dedup(self, messages: List[Message]) -> List[Message]:
        print("start dedup")
        print(len(messages))
        # Normalize content by stripping whitespace and converting to lowercase
        normalized_content = lambda message: message.content.strip().lower()

        # Sort messages by created_at timestamp to ensure earlier messages are prioritized
        messages.sort(key=lambda message: message.created_at)
        print("sorted messages")

        unique_contents = set()
        deduplicated_messages = []
        for message in messages:
            content_key = normalized_content(message)
            if content_key not in unique_contents:
                unique_contents.add(content_key)
                deduplicated_messages.append(message)
        print(f"unique count: {len(deduplicated_messages)}")
        print(f"uniques: {deduplicated_messages}")
        return deduplicated_messages

    def scored_point_to_message(self, scored_point: ScoredPoint) -> Message:
        message_id = scored_point.id
        content = scored_point.payload.get("content", "")
        similarity_score = scored_point.score  # Assuming ScoredPoint has a 'score' attribute
        voice = scored_point.payload.get("voice", 0)
        curations_payload = scored_point.payload.get("curations", [])
        created_at_str = scored_point.payload.get(
            "created_at", datetime.now().isoformat()
        )  # Default to now if not present

        # Convert the creation timestamp string to a datetime object
        created_at = datetime.fromisoformat(created_at_str)

        # Only include voice if it's not 0
        voice = voice if voice != 0 else None

        # Replace list of curations with count, only include if count is not 0
        curations_count = len(curations_payload) if curations_payload else None

        return Message(
            id=message_id,
            content=content,
            similarity_score=similarity_score,
            voice=voice,
            curations_count=curations_count,
            created_at=created_at,
        )

    async def new_message(self, input_text: str) -> MessagesResponse:
        embedding = await self.thoughtspace_data.embed_text(input_text)
        search_results = await self.thoughtspace_data.search_similar_messages(embedding)
        messages = [self.scored_point_to_message(result) for result in search_results]
        await self.thoughtspace_data.upsert_message(str(uuid.uuid4()), input_text, embedding)
        print("before dedup")
        deduped = self.dedup(messages=messages)
        return MessagesResponse(messages=deduped)

    # async def quote_messages(self, id_voice_pairs: dict) -> None:
    #     """
    #     finding the right input and output types is a bit tricky here
    #     """
    #     for message_id, voice in id_voice_pairs.items():
    #         message = await self.thoughtspace_data.get_message(message_id)
    #         if message:
    #             new_voice = message.voice + voice
    #             await self.thoughtspace_data.update_message_voice(message_id, new_voice)

    # async def curate_message(self, point_id: str, quantity_of_voice: int, message: str, user_id: str) -> dict:
    #     """
    #     finding the right input and output types is a bit tricky here
    #     """
    #     new_message_result = await self.new_message(message)
    #     point = await self.thoughtspace_data.get_message(point_id)
    #     if point:
    #         curations = point.curations if point.curations else []
    #         curations.append({"user_id": user_id, "message_id": new_message_result.id})
    #         new_voice = point.voice + quantity_of_voice
    #         await self.thoughtspace_data.update_message_curations_and_voice(point_id, curations, new_voice)
    #     return {"updated_point": point, "new_message_result": new_message_result}
