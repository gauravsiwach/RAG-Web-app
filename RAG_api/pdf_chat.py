import os
from dotenv import load_dotenv
from openai import OpenAI
from query_translation import translate_query
from vector_search import search_and_filter
from guardrails import guardrails_input, guardrails_output
from language_translation import (
    detect_language,
    translate_to_english,
    translate_from_english
)

load_dotenv()

client = OpenAI()


def _get_query_result_pdf_core(query):
    """
    Core PDF chat logic: assumes input is already validated.
    Returns (answer, context) tuple for output guardrail.
    """
    print(f"\n🧠 Original query: '{query}'")

    # Step 1: Translate query into multiple variants for better retrieval
    translated_queries = translate_query(query)

    # Step 2: Search vector DB with all translated queries,
    # filter by relevance score, deduplicate, and rank results
    search_results = search_and_filter(translated_queries, collection_suffix="pdf")

    # Early return if no relevant results found
    if not search_results:
        return ("Sorry, I couldn't find any relevant information for your query in this PDF. Please try asking something related to the document content.", "")

    # Step 3: Build context string from top unique results
    context = "\n\n".join([
        f"Page Content: {doc.page_content}\nPage Number: {doc.metadata.get('page_label', 'Unknown')}"
        for doc, score in search_results
    ])

    SYSTEM_PROMPT = f"""
    You are a helpful AI Assistant who answers user queries based on the available context
    retrieved from a PDF file along with page contents and page number.

    You should only answer the user based on the following context and navigate the user
    to open the right page number to know more.

    Context:
    {context}
    """

    print(f"\n📄here is the Context for LLM: {context}")

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


def get_query_result_pdf(query):
    """
    Wrapper for PDF chat: handles multi-language support, applies guardrails, and delegates to core logic.
    """
    try:
        # Step 1: Detect language and translate to English if needed
        detected_lang = detect_language(query)
        print(f"🌍 Detected language: {detected_lang}")
        
        if detected_lang != "en":
            print(f"🔄 Translating query to English for processing...")
            english_query, _ = translate_to_english(query, detected_lang)
            original_lang = detected_lang
        else:
            print(f"✅ Query is in English, no translation needed.")
            english_query = query
            original_lang = "en"
        
        # Step 2: INPUT guardrail — reject bad queries before any LLM/vector calls
        input_check = guardrails_input(english_query)
        if not input_check["passed"]:
            error_msg = input_check["message"]
            # Translate error back if needed
            if original_lang != "en":
                error_msg = translate_from_english(error_msg, original_lang)
            return error_msg

        # Step 3: Core logic (returns answer, context)
        answer, context = _get_query_result_pdf_core(english_query)

        # Step 4: If context is empty, this is a fallback (no LLM call made)
        if not context:
            if original_lang != "en":
                answer = translate_from_english(answer, original_lang)
            return answer

        # Step 5: OUTPUT guardrail — relevance check before returning
        final_answer = guardrails_output(english_query, answer, context)
        
        # Step 6: Translate response back to original language if needed
        if original_lang != "en":
            final_answer = translate_from_english(final_answer, original_lang)
        
        return final_answer

    except Exception as e:
        print(f"❌ Error in get_query_result_pdf: {e}")
        return "Sorry, there was an error processing your query. Please try again."


     
