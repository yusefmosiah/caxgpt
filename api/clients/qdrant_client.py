import os
import logging
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import ApiException, UnexpectedResponse

class QdrantClient:
    def __init__(self, collection_name="choir", qdrant_url=None, qdrant_api_key=None):
        self.qdrant_url = qdrant_url if qdrant_url else os.environ.get("QDRANT_URL")
        self.qdrant_api_key = qdrant_api_key if qdrant_api_key else os.environ.get("QDRANT_API_KEY")
        self.client = AsyncQdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key)
        self.collection_name = collection_name

    async def search(self, embedding, search_limit=200, with_vectors=False):
        try:
            search_results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                limit=search_limit,
                with_vectors=with_vectors,
            )
            return search_results
        except (ApiException, UnexpectedResponse) as e:
            logging.error(f"Error during search operation: {e}")
            # Handle the error as needed, e.g., retry, return a default value, etc.
            return None

    async def retrieve(self, ids):
        try:
            return await self.client.retrieve(collection_name=self.collection_name, ids=ids)
        except (ApiException, UnexpectedResponse) as e:
            logging.error(f"Error during retrieve operation: {e}")
            return None

    async def set_payload(self, payload, points):
        try:
            await self.client.set_payload(collection_name=self.collection_name, payload=payload, points=points)
        except (ApiException, UnexpectedResponse) as e:
            logging.error(f"Error during set_payload operation: {e}")
            # Decide on how to handle the error

    async def upsert(self, id, input_string, embedding):
        try:
            await self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=id,
                        payload={"content": input_string},
                        vector=embedding,
                    )
                ],
            )
        except (ApiException, UnexpectedResponse) as e:
            logging.error(f"Error during upsert operation: {e}")
            # Handle the error as needed
