import os
from dotenv import load_dotenv
from openai import OpenAI
from query_translation import translate_query
from vector_search import search_and_filter
from guardrails import guardrails_input, guardrails_output


load_dotenv()

client = OpenAI()


def _get_query_result_web_core(query):
    """
    Core Web URL chat logic: assumes input is already validated.
    Returns (answer, context) tuple for output guardrail.
    """
    print(f"\n🧠 Original query: '{query}'")

    # Step 1: Translate query into multiple variants for better retrieval
    translated_queries = translate_query(query)

    # Step 2: Search vector DB with all translated queries,
    # filter by relevance score, deduplicate, and rank results
    search_results = search_and_filter(translated_queries, collection_suffix="url")

    if not search_results:
        return ("Sorry, I couldn't find any relevant information for your query in this web page. Try asking something related to the page content.", "")

    # Step 3: Build context string from top unique results
    context = "\n\n".join([
        f"Page Content: {doc.page_content}"
        for doc, score in search_results
    ])

    SYSTEM_PROMPT = f"""
    You are a helpful AI Assistant who answers user queries based on the available context
    retrieved from a web page.

    You should only answer the user based on the following context.

    Context:
    {context}
    """

    # Step 4: Call OpenAI LLM with context + user query
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ]
    )
    answer = response.choices[0].message.content
    print(f"\n🤖: {answer}")
    return (answer, context)


def get_query_result_web(query):
    """
    Wrapper for Web URL chat: applies input/output guardrails and delegates to core logic.
    """
    try:
        # INPUT guardrail — reject bad queries before any LLM/vector calls
        input_check = guardrails_input(query)
        if not input_check["passed"]:
            return input_check["message"]

        # Core logic (returns answer, context)
        answer, context = _get_query_result_web_core(query)

        # If context is empty, this is a fallback (no LLM call made)
        if not context:
            return answer

        # OUTPUT guardrail — relevance check before returning
        final_answer = guardrails_output(query, answer, context)
        return final_answer

    except Exception as e:
        print(f"❌ Error in get_query_result_web: {e}")
        return "Sorry, there was an error processing your query. Please try again."

