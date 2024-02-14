import os
from qdrant_client import AsyncQdrantClient, models
from openai import AsyncOpenAI
import uuid


class ThoughtSpace:
    def __init__(
        self,
        collection_name="choir",
        openai_api_key=None,
        qdrant_url=None,
        qdrant_api_key=None,
    ):
        # Use provided API keys or source from environment
        self.openai_api_key = openai_api_key if openai_api_key else os.environ.get("OPENAI_API_KEY")
        self.qdrant_url = qdrant_url if qdrant_url else os.environ.get("QDRANT_URL")
        self.qdrant_api_key = qdrant_api_key if qdrant_api_key else os.environ.get("QDRANT_API_KEY")

        self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
        self.qdrant_client = AsyncQdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key)
        self.collection_name = collection_name

    async def embed(self, input_text, model_name="text-embedding-ada-002"):
        embedding_response = await self.openai_client.embeddings.create(input=input_text, model=model_name)
        return embedding_response.data[0].embedding

    async def search(self, embedding, search_limit=200, with_vectors=False):
        search_results = await self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=embedding,
            limit=search_limit,
            with_vectors=with_vectors,
        )
        return search_results

    @staticmethod
    def deduplicate(results):
        unique_payloads = set()
        deduplicated_results = []
        for result in results:
            payload_content = result.payload.get("content", "")
            if payload_content not in unique_payloads:
                unique_payloads.add(payload_content)
                deduplicated_results.append(result)
        return deduplicated_results

    async def retrieve(self, ids):
        return await self.qdrant_client.retrieve(collection_name=self.collection_name, ids=ids)

    async def set_payload(self, payload, points):
        """
        Sets payload data for specific points in the collection.

        Parameters:
        - payload (dict): The payload data to set.
        - points (list): A list of point IDs to which the payload data will be applied.
        """
        await self.qdrant_client.set_payload(collection_name=self.collection_name, payload=payload, points=points)

    async def process_query(
        self,
        query,
        model_name="text-embedding-ada-002",
        search_limit=200,
        with_vectors=False,
    ):
        embedding = await self.embed(query, model_name)
        search_results = await self.search(embedding, search_limit, with_vectors)
        deduplicated_results = self.deduplicate(search_results)
        return deduplicated_results

    async def new_message(self, input_string, id=str(uuid.uuid4())):
        """
        Processes a new message by embedding it, searching for similar messages, upserting the new message into the collection, and returning deduplicated search results.

        Parameters:
        - input_string (str): The message to be processed.

        Returns:
        - list: A list of deduplicated search results.
        """
        # Embed the input string
        embedding = await self.embed(input_string)
        # Perform a similarity search with the embedding
        search_results = await self.search(embedding)
        # Upsert the input string into the collection
        await self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=id,  # Generate a unique ID for the new document
                    payload={"content": input_string},  # include other stuff here???
                    vector=embedding,
                )
            ],
        )
        # Return the list of search results
        return self.deduplicate(search_results)

    async def quote_messages(self, id_voice_pairs):
        """
        Updates the payload of messages with a new or updated "voice" value.

        Parameters:
        - id_voice_pairs (dict): A dictionary where keys are message IDs and values are the voice scores to be added or updated.
        """
        # Retrieve existing payloads for the given IDs
        points = await self.retrieve(ids=list(id_voice_pairs.keys()))

        # Prepare updates
        updates = []
        for point in points:
            # Check if 'voice' exists in the payload and access it, otherwise default to 0
            current_voice = point.payload.get("voice", 0) if isinstance(point.payload, dict) else 0
            # Calculate the new voice value
            new_voice = current_voice + id_voice_pairs.get(point.id, 0)
            # Prepare the updated payload with the new voice value
            updated_payload = {"voice": new_voice}
            # Append the update to the list
            updates.append((point.id, updated_payload))

        # Apply updates
        for point_id, new_payload in updates:
            await self.set_payload(payload=new_payload, points=[point_id])

        return updates

    async def curate_message(self, point_id, quantity_of_voice, message, user_id):
        """
        Curates a message by adding a user's message ID to a point's payload, updating the 'voice' amount,
        and inserting the message into the collection. Returns the updated point and the result of the new message insertion.

        Parameters:
        - point_id (str): The UUID of the point to curate.
        - quantity_of_voice (int): The quantity of voice to add to the existing 'voice' amount.
        - message (str): The message from the user.
        - user_id (str): The ID of the user curating the message.

        Returns:
        - dict: A dictionary containing the updated point and the result of calling new_message.
        """
        message_id = str(uuid.uuid4())
        new_message_result = await self.new_message(message, id=message_id)

        points = await self.retrieve(ids=[point_id])
        if not points:
            return None  # Handle the case where the point does not exist

        point = points[0]
        curations = point.payload.get("curations", [])
        current_voice = point.payload.get("voice", 0)

        curations.append({"user_id": user_id, "message_id": message_id})
        new_voice = current_voice + quantity_of_voice
        updated_payload = {**point.payload, "curations": curations, "voice": new_voice}

        point.payload = updated_payload

        await self.set_payload(payload=updated_payload, points=[point_id])

        return {"updated_point": point, "new_message_result": new_message_result}
