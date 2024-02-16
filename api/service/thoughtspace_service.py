from typing import List
from ..data.thoughtspace_data import ThoughtSpaceData
from ..models._message import Message, Curation, MessagesResponse
from datetime import datetime
from qdrant_client.http.models import ScoredPoint
from sqlalchemy.orm import Session
import math
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

    def dedup(self, messages: List[Message]) -> List[Message]:
        # Normalize content by stripping whitespace and converting to lowercase
        normalized_content = lambda message: message.content.strip().lower()

        # Sort messages by created_at timestamp to ensure earlier messages are prioritized
        messages.sort(key=lambda message: message.created_at)

        unique_contents = set()
        deduplicated_messages = []
        for message in messages:
            content_key = normalized_content(message)
            if content_key not in unique_contents:
                unique_contents.add(content_key)
                deduplicated_messages.append(message)
        return deduplicated_messages

    def rerank(self, messages):
        now = datetime.now()
        for msg in messages:
            # Check if msg.voice is None and default to 1 before applying sqrt
            voice_value = 1 if msg.voice is None else msg.voice**0.1
            # Use voice_value in the calculation, which will be 1 if msg.voice was None
            msg.reranking_score = ((100 * msg.similarity_score * voice_value) ** (msg.curations_count or 1.0)) / (
                now - msg.created_at
            ).total_seconds()
        return sorted(messages, key=lambda msg: msg.reranking_score, reverse=True)

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

    def record_to_message(self, record):
        message_id = record.id
        content = record.payload.get("content", "")
        # Assuming there's no similarity_score in the record, so we set a default or calculate it differently
        similarity_score = 0  # or some other default value or calculation
        voice = record.payload.get("voice", 0)  # Assuming voice might be in the payload
        curations_payload = record.payload.get("curations", [])
        created_at_str = record.payload.get("created_at", datetime.now().isoformat())

        created_at = datetime.fromisoformat(created_at_str)
        voice = voice if voice != 0 else None
        curations_count = len(curations_payload) if curations_payload else None

        return Message(
            id=message_id,
            content=content,
            similarity_score=similarity_score,
            voice=voice,
            curations_count=curations_count,
            created_at=created_at,
        )

    def message_to_sparse_dict(self, message):
        # Ensure default values for similarity_score and reranking_score if they are None
        similarity_score = message.similarity_score if message.similarity_score is not None else 1
        reranking_score = message.reranking_score if message.reranking_score is not None else 1

        fields = {
            "id": str(message.id),
            "content": message.content,
            "reranking": reranking_score,
            "similarity": similarity_score,
            "voice": message.voice,
            "curations_count": message.curations_count,
            "novelty": math.sqrt((1 - similarity_score) * reranking_score),
        }
        return {k: v for k, v in fields.items() if v is not None}

    def records_to_sparse_dicts(self, records):

        messages = [self.record_to_message(record) for record in records]
        print(f"messages {messages}")
        # Assuming reranking_score and other calculations are handled elsewhere or set to defaults
        sparse_dicts = [self.message_to_sparse_dict(message) for message in messages]
        print(f"sparse_dicts {sparse_dicts}")
        return sparse_dicts

    def calculate_novelty(self, search_results):
        print(f"novelty {search_results[:10]}")
        novelty_scores = [1 - result.score for result in search_results]
        return novelty_scores

    async def new_message(self, input_text: str, user_id: str):
        embedding = await self.thoughtspace_data.embed_text(input_text)
        search_results = await self.thoughtspace_data.search_similar_messages(embedding)
        messages = [self.scored_point_to_message(result) for result in search_results]
        # save message to database
        message_id = str(uuid.uuid4())
        await self.thoughtspace_data.upsert_message(message_id, input_text, embedding)
        print("after upsert")
        self.thoughtspace_data.create_message(user_id, message_id)
        print("after create_message")

        # Deduplicate and rerank messages
        relevant_messages = self.rerank(self.dedup(messages))
        print("after relevant_messages")
        # Convert messages to sparse format
        sparse_messages = [self.message_to_sparse_dict(msg) for msg in relevant_messages]
        print("after sparse_messages")

        # Calculate total novelty score
        total_novelty = sum(math.sqrt((1 - msg.similarity_score) * msg.reranking_score) for msg in relevant_messages)
        # "novelty": (1 - message.similarity_score) * message.reranking_score,
        print("after total_novelty")
        self.thoughtspace_data.update_user_voice_balance(user_id, total_novelty)
        return {"novelty": total_novelty, "messages": sparse_messages}

    async def get_dashboard_data(self, user_id: str):
        # Fetch user voice balance and message IDs from the database
        user_data = self.thoughtspace_data.get_user_voice_balance_and_messages(user_id)
        if not user_data:
            return None  # Or handle the case where the user or messages are not found

        # Retrieve messages from Qdrant using the message IDs
        msg_ids = [str(msg_id) for msg_id in user_data["message_ids"]]
        records = await self.thoughtspace_data.retrieve_messages(msg_ids)
        print("after retreive")

        # Convert the retrieved records to Message instances, then to sparse dictionaries
        sparse_messages = self.records_to_sparse_dicts(records)

        # Return the user's voice balance and their messages in sparse dictionary form
        return {"voice_balance": user_data["voice_balance"], "messages": sparse_messages}

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
