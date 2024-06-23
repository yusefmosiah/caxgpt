from openai import OpenAI
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import ApiException, UnexpectedResponse
from datetime import datetime
import logging
import uuid
import os

openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
qdrant_client = QdrantClient(url=os.environ.get("QDRANT_URL"), api_key=os.environ.get("QDRANT_API_KEY"))

def embed(input_text, model_name="text-embedding-ada-002", chunk_size=10000, overlap=5000):
    chunks = []
    start = 0
    while start < len(input_text):
        end = min(start + chunk_size, len(input_text))
        chunks.append(input_text[start:end])
        start += chunk_size - overlap

    embeddings = []
    for chunk in chunks:
        embedding_response = openai_client.embeddings.create(
            input=chunk,
            model=model_name
        )
        embeddings.append(embedding_response.data[0].embedding)

    return embeddings

def search(embeddings, collection_name="choir", search_limit=40):
    search_results = []
    for embedding in embeddings:
        results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=embedding,
            limit=search_limit
        )
        search_results.extend(results)

    return search_results

def deduplicate(search_results):
    unique_payloads = set()
    deduplicated_results = []
    for result in search_results:
        payload_content = result.payload.get('content', None)
        if payload_content and payload_content not in unique_payloads:
            unique_payloads.add(payload_content)
            deduplicated_results.append(result)

    print(f"Deduplicated {len(search_results)} search results to {len(deduplicated_results)} unique results: {deduplicated_results}")
    return deduplicated_results

def chat_completion(messages, model="gpt-4o", max_tokens=4000, n=1, stop=None, temperature=0.7):
    response = openai_client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        n=n,
        stop=stop,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()

def upsert(id, input_string, embedding, collection_name="choir"):
        try:
            qdrant_client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=id,
                        payload={"content": input_string, "created_at": datetime.now(), "agent": "vowel_loop_v0"},
                        vector=embedding,
                    )
                ],
            )
            print(f"Successfully upserted observation with ID: {id}, content: {input_string}")
        except (ApiException, UnexpectedResponse) as e:
            logging.error(f"Error during upsert operation: {e}")
            # Handle the error as needed

def save_observation(observation):
    try:
        embedding = embed(observation)
        observation_id = str(uuid.uuid4())  # Generate a unique ID for the observation

        upsert(
            id=observation_id,
            input_string=observation,
            embedding=embedding
        )

    except Exception as e:
        logging.error(f"Error during save_observation: {e}")
        # Handle the error as needed

def action(messages, user_prompt):
    action_system_prompt = """
    This is the Vowel Loop, a decision-making model that turns the OODA loop on its head. Rather than accumulating data before acting, you act with "beginners mind"/emptiness, then reflect on your "System 1" action.
    A user has asked you to engage in the Vowel Loop reasoning process.
    This is step 1, Action: Provide an initial response to the user's prompt to the best of your ability.
    """

    messages = [{"role": "system", "content": action_system_prompt}, {"role": "user", "content": user_prompt}]
    completion = chat_completion(messages)
    print(f"Action: {completion}")
    return completion

def experience(messages):
    experience_system_prompt = """This is step 2 of the Vowel Loop, Experience: Search your memory for relevant context that could help refine the response from step 1."""

    prompt = messages[-1]["content"]
    embedding = embed(prompt)
    search_results = search(embedding)
    deduplicated_results = deduplicate(search_results)

    reranked_prompt = f"{prompt}\n\nSearch Results:\n{[r.payload['content'] for r in deduplicated_results]}\n\nReranked Search Results:"
    messages = [{"role": "system", "content": experience_system_prompt}, {"role": "user", "content": reranked_prompt}]
    completion = chat_completion(messages)
    print(f"Experience: {completion}")
    return completion

def intention(messages):
    intention_system_prompt = """
    This is step 3 of the Vowel Loop, Intention: Impute the user's intention, reflecting on whether the query can be satisfactorily responded to based on the priors recalled in the Experience step
    """

    intention_prompt = f"{messages[-1]['content']}\n\nReflection on goal satisfiability:"
    messages = [{"role": "system", "content": intention_system_prompt}, {"role": "user", "content": intention_prompt}]
    completion = chat_completion(messages)
    print(f"Intention: {completion}")
    return completion

def observation(messages):
    observation_system_prompt = """This is step 4 of the Vowel Loop, Observation: Note any key insights from this iteration that could help improve future responses.
    This note will be saved to a global vector database accessible to all instances of this AI Agent, for all users.
    Don't save any private information."""

    observation_prompt = f"{messages[-1]['content']}\n\nNote for future recall:"
    messages = [{"role": "system", "content": observation_system_prompt}, {"role": "user", "content": observation_prompt}]
    completion = chat_completion(messages)
    print(f"Observation: {completion}")
    return completion

def update(messages):
    update_system_prompt = """This is step 5 of the Vowel Loop, Update: Decide whether to perform another round of the loop to further refine the response or to provide a final answer to the user. Respond with 'LOOP' or 'RETURN'."""

    update_prompt = f"{messages[-1]['content']}\n\nShould we LOOP or RETURN final response?"
    messages = [{"role": "system", "content": update_system_prompt}, {"role": "user", "content": update_prompt}]
    completion = chat_completion(messages, max_tokens=1)
    print(f"Update: {completion}")

    observation_result = messages[-2]["content"].replace("Observation: ", "")
    save_observation(observation_result)

    if completion.lower() == "return":
        return "return"
    elif completion.lower() == "loop":
        print("Looping...\n")
        return "loop"
    else:
        print("Invalid update response. Please try again.")
        return "invalid"

def yield_response(messages):
    yield_system_prompt = """This is the final step of the Vowel Loop, Yield: Synthesize the accumulated context from all iterations and provide a final response that comprehensively addresses the user's original prompt."""
    messages.append({"role": "system", "content": yield_system_prompt})
    messages.append({"role": "user", "content": "Synthesize the accumulated context and provide a final response:"})
    final_response = chat_completion(messages)
    return final_response

def vowel_loop(user_prompt):
    messages = []
    while True:
        action_result = action(messages, user_prompt)
        messages.append({"role": "assistant", "content": f"Action: {action_result}"})
        experience_result = experience(messages)
        messages.append({"role": "assistant", "content": f"Experience: {experience_result}"})
        intention_result = intention(messages)
        messages.append({"role": "assistant", "content": f"Intention: {intention_result}"})
        observation_result = observation(messages)
        messages.append({"role": "assistant", "content": f"Observation: {observation_result}"})
        update_result = update(messages)
        if update_result == "return":
            break
        else:
            continue
    final_response = yield_response(messages)
    return final_response
