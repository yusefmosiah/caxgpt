from typing import List
from ..data.thoughtspace_data import ThoughtSpaceData
from ..models._message import Message, MessagesResponse
from datetime import datetime
from qdrant_client.http.models import ScoredPoint


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
        """
        Deduplicates a list of messages based on content, choosing the one with the earliest created_at timestamp in case of duplicates.
        """
        # Sort messages by created_at timestamp to ensure earlier messages are prioritized
        messages.sort(key=lambda message: message.created_at)
        # Use an ordered dictionary to deduplicate, preserving the order and prioritizing earlier messages
        unique_messages = list({message.content: message for message in messages}.values())
        return unique_messages

    # Additional methods for curating messages, etc., can be added here

    def scored_point_to_message(self, scored_point: ScoredPoint) -> Message:
        """
        Converts a single ScoredPoint from Qdrant search results into a Message model, including curations.
        Extracts the 'created_at' timestamp from the payload and uses it for both 'created_at' and 'updated_at' fields.
        """
        message_id = scored_point.id
        content = scored_point.payload.get("content", "")
        voice = scored_point.payload.get("voice", 0)
        curations_payload = scored_point.payload.get("curations", [])
        created_at_str = scored_point.payload.get(
            "created_at", datetime.now().isoformat()
        )  # Default to now if not present

        # Convert the creation timestamp string to a datetime object
        created_at = datetime.fromisoformat(created_at_str)

        # Process curations if available
        curations = []
        for curation_data in curations_payload:
            try:
                curation = Curation(**curation_data)
                curations.append(curation)
            except TypeError:
                # If curation_data does not match the Curation model, skip it
                continue

        return Message(
            id=message_id,
            content=content,
            voice=voice,
            curations=curations,
            created_at=created_at,
        )

    async def new_message(self, input_text: str) -> MessagesResponse:
        embedding = await self.thoughtspace_data.embed_text(input_text)
        search_results = await self.thoughtspace_data.search_similar_messages(embedding)
        messages = [self.scored_point_to_message(result) for result in search_results]
        await self.thoughtspace_data.upsert_message(str(uuid.uuid4()), input_text, embedding)
        return MessagesResponse(messages=messages)

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
