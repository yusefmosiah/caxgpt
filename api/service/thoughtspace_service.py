from typing import List
from ..data.thoughtspace_data import ThoughtSpaceData
from ..models._message import Message, MessagesResponse
from datetime import datetime
from qdrant_client.http.models import ScoredPoint


class ThoughtSpaceService:
    def __init__(self, thoughtspace_data: ThoughtSpaceData):
        self.thoughtspace_data = thoughtspace_data

    async def embed_and_search_messages(
        self, input_text: str, search_limit: int = 200, with_vectors: bool = False
    ) -> MessagesResponse:
        """
        Embeds the input text using OpenAI, searches for similar messages using Qdrant, and returns the search results.
        """
        embedding = await self.thoughtspace_data.embed_text(input_text)
        search_results = await self.thoughtspace_data.search_similar_messages(embedding, search_limit, with_vectors)
        # Convert search results to MessagesResponse format
        # This step requires processing the search results to fit the Message model
        messages = self.process_search_results_to_messages(search_results)
        return MessagesResponse(messages=messages)

    async def deduplicate_messages(self, messages: List[Message]) -> List[Message]:
        """
        Deduplicates a list of messages based on content or other criteria.
        """
        # Implement deduplication logic
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

    def process_search_results_to_messages(self, search_results: List[ScoredPoint]) -> List[Message]:
        """
        Processes search results from Qdrant and converts them into a list of Message models by calling scored_point_to_message for each result.
        """
        return [self.scored_point_to_message(result) for result in search_results]
