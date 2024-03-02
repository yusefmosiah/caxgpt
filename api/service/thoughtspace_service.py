from typing import List

# import tiktoken
from ..data.thoughtspace_data import ThoughtSpaceData
from ..models._message import Message, Revision, MessagesResponse, RevisionRequest
from datetime import datetime
from qdrant_client.http.models import ScoredPoint
from sqlalchemy.orm import Session
import math
import uuid
import logging

logger = logging.getLogger(__name__)


class ThoughtSpaceService:
    def __init__(self, db: Session):
        self.thoughtspace_data = ThoughtSpaceData(db=db)

    async def embed_and_search_messages(
        self, input_text: str, search_limit: int = 200, with_vectors: bool = False
    ) -> MessagesResponse:
        try:
            embedding = await self.thoughtspace_data.embed_text(input_text)
            search_results = await self.thoughtspace_data.search_similar_messages(embedding, search_limit, with_vectors)
            messages = [self.scored_point_to_message(result) for result in search_results]
            return MessagesResponse(messages=messages)
        except Exception as e:
            logger.error(f"Failed to embed and search messages: {e}")
            raise

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
        print("reranking")
        now = datetime.now()
        for msg in messages:
            # Check if msg.voice is None and default to 1 before applying sqrt
            voice_value = 1 if msg.voice is None else msg.voice**0.1
            # Use voice_value in the calculation, which will be 1 if msg.voice was None
            rerank = ((100 * msg.similarity_score * voice_value) ** (msg.revisions_count or 1.0)) / (
                now - msg.created_at
            ).total_seconds()
            rerank_adjusted = rerank + 1  # in case 0 < rerank < 1
            msg.reranking_score = math.log(rerank_adjusted)

        print("done ranking")
        return sorted(messages, key=lambda msg: msg.reranking_score, reverse=True)

    def scored_point_to_message(self, scored_point: ScoredPoint) -> Message:
        try:
            if isinstance(scored_point.id, int):
                logger.info("scored_point.id is int, handling case")
                message_id = uuid.uuid4()
            else:
                message_id = uuid.UUID(scored_point.id)
        except ValueError:
            logger.error(f"Invalid UUID format: {scored_point.id}")
            message_id = uuid.uuid4()  # Fallback to generating a new UUID

        content = scored_point.payload.get("content", "")
        similarity_score = scored_point.score  # Assuming ScoredPoint has a 'score' attribute
        voice = scored_point.payload.get("voice", 0)
        revisions_payload = scored_point.payload.get("revisions", [])
        created_at_str = scored_point.payload.get(
            "created_at", datetime.now().isoformat()
        )  # Default to now if not present

        # Convert the creation timestamp string to a datetime object
        created_at = datetime.fromisoformat(created_at_str)

        # Only include voice if it's not 0
        voice = voice if voice != 0 else None

        # Replace list of revisions with count, only include if count is not 0
        revisions_count = len(revisions_payload) if revisions_payload else None

        return Message(
            id=message_id,
            content=content,
            similarity_score=similarity_score,
            voice=voice,
            revisions_count=revisions_count,
            created_at=created_at,
        )

    def record_to_message(self, record):
        message_id = record.id
        content = record.payload.get("content", "")
        # Assuming there's no similarity_score in the record, so we set a default or calculate it differently
        similarity_score = 0  # or some other default value or calculation
        voice = record.payload.get("voice", 0)  # Assuming voice might be in the payload
        revisions_payload = record.payload.get("revisions", [])
        created_at_str = record.payload.get("created_at", datetime.now().isoformat())

        created_at = datetime.fromisoformat(created_at_str)
        voice = voice if voice != 0 else None
        revisions_count = len(revisions_payload) if revisions_payload else None

        return Message(
            id=message_id,
            content=content,
            similarity_score=similarity_score,
            voice=voice,
            revisions_count=revisions_count,
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
            "revisions_count": message.revisions_count,
            # similarity score for exact matches = 1.000001, and this messes with math
            "novelty": math.sqrt((1.0001 - similarity_score) * reranking_score),
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

    async def reward_authors_of_relevant_messages(self, relevant_messages):
        print("reward_authors_of_relevant_messages")
        voice_rewards = {}  # Dictionary to hold aggregated voice rewards

        # Step 1: Batch fetch user IDs for message authors
        message_ids = [str(msg.id) for msg in relevant_messages]
        message_user_mapping = self.thoughtspace_data.get_messages_user_mapping(message_ids)

        # Process each message_id in the mapping
        for message_id, author_id in message_user_mapping.items():
            # Find the relevant message object to calculate its voice reward
            relevant_message = next((msg for msg in relevant_messages if str(msg.id) == message_id), None)
            if relevant_message is None:
                print("relevant_message is none")
                continue  # Skip if the message object is not found in the relevant_messages list

            voice_reward = self.calculate_voice_reward(relevant_message)

            # Aggregate voice rewards by author_id
            if author_id in voice_rewards:
                voice_rewards[author_id] += voice_reward
            else:
                voice_rewards[author_id] = voice_reward

        # Bulk update voice balances
        self.thoughtspace_data.bulk_update_user_voice_balances(voice_rewards)
        print(f"Processed rewards for {len(message_user_mapping)} messages")
        # Bulk update voice balances

    def calculate_voice_reward(self, message):
        # Example reward calculation based on reranking score
        # Ensure reranking_score is initialized and not None
        reranking_score = message.reranking_score if message.reranking_score is not None else 0

        # Simple reward calculation: a base reward plus a multiplier of the reranking score
        # Adjust the base_reward and multiplier as needed
        base_reward = 1  # Minimum reward
        multiplier = 0.5  # Adjust based on how much you want the reranking score to influence the reward

        # Calculate the reward
        reward = base_reward + (multiplier * reranking_score)

        # Ensure the reward is a positive number
        reward = max(reward, 0)
        print(f"reward {reward} for message {message.id}")

        return reward

    async def new_message(self, input_text: str, user_id: str):
        embedding = await self.thoughtspace_data.embed_text(input_text)
        search_results = await self.thoughtspace_data.search_similar_messages(embedding)
        messages = [self.scored_point_to_message(result) for result in search_results]
        message_id = str(uuid.uuid4())
        await self.thoughtspace_data.upsert_message(message_id, input_text, embedding)
        self.thoughtspace_data.create_message(user_id, message_id)
        relevant_messages = self.rerank(self.dedup(messages))
        self.reward_authors_of_relevant_messages(relevant_messages)
        sparse_messages = [self.message_to_sparse_dict(msg) for msg in relevant_messages]
        # token_count = len(tiktoken.get_encoding("cl100k_base").encode(input_text))
        token_count = 100
        self.thoughtspace_data.update_user_voice_balance(user_id, token_count)

        return {"token_count": token_count, "messages": sparse_messages}

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

    async def search(self, input_text: str) -> List[dict]:
        # Embed the input text
        embedding = await self.thoughtspace_data.embed_text(input_text)
        # Search Qdrant for similar messages
        search_results = await self.thoughtspace_data.search_similar_messages(embedding)
        # Convert search results to Message instances
        messages = [self.scored_point_to_message(result) for result in search_results]
        # Deduplicate and rerank messages
        resonant_messages = self.rerank(self.dedup(messages))
        # Convert messages to sparse format
        # sparse_messages = [self.message_to_sparse_dict(msg) for msg in resonant_messages]
        # print("sparse now")
        return resonant_messages

    # async def propose_revision(self, revision_request: RevisionRequest, user_id: str):
    #     # Validate the message_id and check if the message exists
    #     # Update the message with revised_text
    #     # Adjust the user's voice balance based on the voice parameter
    #     # Return a response indicating success or failure
    #     return 0
