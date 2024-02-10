import os
from qdrant_client import QdrantClient
from qdrant_client.http import models
from openai import OpenAI

class ThoughtSpace:
    def __init__(self, collection_name, openai_api_key=None, qdrant_url=None, qdrant_api_key=None):
        # Use provided API keys or source from environment
        self.openai_api_key = openai_api_key if openai_api_key else os.environ.get("OPENAI_API_KEY")
        self.qdrant_url = qdrant_url if qdrant_url else os.environ.get("QDRANT_URL")
        self.qdrant_api_key = qdrant_api_key if qdrant_api_key else os.environ.get("QDRANT_API_KEY")

        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.qdrant_client = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key)
        self.collection_name = collection_name

    def embed(self, input_text, model_name="text-embedding-ada-002"):
        embedding_response = self.openai_client.embeddings.create(
            input=input_text,
            model=model_name
        )
        return embedding_response.data[0].embedding

    def search(self, embedding, search_limit=200, with_vectors=False):
        search_results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=embedding,
            limit=search_limit,
            with_vectors=with_vectors
        )
        return search_results

    def deduplicate(self, results):
        unique_payloads = set()
        deduplicated_results = []
        for result in results:
            payload_content = result.payload.get('content', '')
            if payload_content not in unique_payloads:
                unique_payloads.add(payload_content)
                deduplicated_results.append(result)
        return deduplicated_results

    def retrieve(self, ids):
        return self.qdrant_client.retrieve(collection_name=self.collection_name, ids=ids)

    def process_query(self, query, model_name="text-embedding-ada-002", search_limit=200, with_vectors=False):
        embedding = self.embed(query, model_name)
        search_results = self.search(embedding, search_limit, with_vectors)
        deduplicated_results = self.deduplicate(search_results)
        return deduplicated_results
