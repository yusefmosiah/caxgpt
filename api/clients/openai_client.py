import os
from openai import AsyncOpenAI, OpenAIError

class OpenAIClient:
    def __init__(self, openai_api_key=None):
        self.openai_api_key = openai_api_key if openai_api_key else os.environ.get("OPENAI_API_KEY")
        try:
            self.client = AsyncOpenAI(api_key=self.openai_api_key)
        except OpenAIError as e:
            print(f"Failed to initialize OpenAI client: {e}")
            self.client = None

    async def embed(self, input_text, model_name="text-embedding-ada-002"):
        if not self.client:
            print("OpenAI client is not initialized.")
            return None
        try:
            embedding_response = await self.client.embeddings.create(input=input_text, model=model_name)
            return embedding_response.data[0].embedding
        except OpenAIError as e:
            print(f"Failed to retrieve embedding: {e}")
            return None
