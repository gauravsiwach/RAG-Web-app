import os
from dotenv import load_dotenv
from openai import OpenAI
from query_translation import translate_query
from vector_search import search_and_filter
from response_judge import evaluate_and_filter_response

load_dotenv()

client = OpenAI()


def get_query_result_pdf(query):
    try:
        print(f"\n🧠 Original query: '{query}'")

        # Step 1: Translate query into multiple variants for better retrieval
        # (multi-query, step-back, sub-queries)
        translated_queries =  translate_query(query)



        # Step 2: Search vector DB with all translated queries,
        # filter by relevance score, deduplicate, and rank results
        search_results = search_and_filter(translated_queries, collection_suffix="pdf")

        # if not search_results:
        #     return "Sorry, I couldn't find any relevant information for your query in this PDF. Try asking something related to the document content."

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
        
        # Step 5: Use LLM judge to evaluate response relevance
        final_answer = evaluate_and_filter_response(query, answer, context)
        return final_answer

    except Exception as e:
        print(f"❌ Error in get_query_result_pdf: {e}")
        return "Sorry, there was an error processing your query. Please try again."


     
