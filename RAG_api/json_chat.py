import os
from dotenv import load_dotenv
from openai import OpenAI
from query_translation import translate_query
from vector_search import search_and_filter

load_dotenv()

client = OpenAI()


def get_query_result_json(query):
    try:
        print(f"\n🧠 Original query: '{query}'")

        # Step 1: Translate query into multiple variants for better retrieval
        translated_queries = translate_query(query)

        # Step 2: Search vector DB with all translated queries,
        # filter by relevance score, deduplicate, and rank results
        search_results = search_and_filter(translated_queries, collection_suffix="json")

        if not search_results:
            return "Sorry, I couldn't find any relevant information for your query in this JSON file. Try asking something related to the data content."

        # Step 3: Build context string from top unique results
        context = "\n\n".join([
            f"Data:\n{doc.page_content}"
            for doc, score in search_results
        ])

        SYSTEM_PROMPT = f"""
        You are a helpful AI Assistant who answers user queries based on the available context
        retrieved from a JSON data file.

        You MUST respond ONLY with a valid JSON object in the following format:
        {{
          "summary": "<one or two sentence answer to the user query>",
          "data": [
            {{ "<field>": "<value>", ... }},
            ...
          ],
          "columns": ["<field1>", "<field2>", ...]
        }}

        Rules:
        - "summary": always include a plain-language answer.
        - "data": include the matching records as an array of objects. If no tabular data is relevant, set to [].
        - "columns": list the keys used in the data rows (same order). If data is [], set to [].
        - Answer ONLY from the context below. Do not invent values.
        - Do NOT wrap the JSON in markdown code fences.

        Context:
        {context}
        """

        # Step 4: Call OpenAI LLM with context + user query, enforcing JSON output
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ]
        )
        answer = response.choices[0].message.content
        print(f"\n🤖: {answer}")
        return answer

    except Exception as e:
        print(f"❌ Error in get_query_result_json: {e}")
        return "Sorry, there was an error processing your query. Please try again."
