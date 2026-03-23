import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

def evaluate_response_relevance(original_query, generated_response, context_used):
    """
    LLM-as-Judge: Evaluates if the generated response is relevant to the original query
    Returns True if relevant, False if not relevant
    """
    try:
        # Judge prompt to evaluate relevance
        JUDGE_SYSTEM_PROMPT = """
        You are an AI judge that evaluates the relevance between a user's query and an AI assistant's response.

        Your task is to determine if the AI assistant's response adequately answers the user's query based on the provided context.

        Evaluation criteria:
        1. Does the response directly address the user's question?
        2. Is the response grounded in the provided context?
        3. Does the response provide useful information related to the query?
        4. Is the response specific enough to be helpful?

        Respond with ONLY one word:
        - "RELEVANT" if the response adequately answers the query
        - "IRRELEVANT" if the response does not adequately answer the query

        Be strict in your evaluation. If the response is generic, vague, or doesn't specifically address the user's question, mark it as IRRELEVANT.
        """

        JUDGE_USER_PROMPT = f"""
        Original User Query: "{original_query}"

        AI Assistant's Response: "{generated_response}"

        Context Used: "{context_used[:1500]}..."

        Evaluation: Is the response relevant to the query?
        """

        # Call LLM judge
        judge_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": JUDGE_USER_PROMPT},
            ],
            temperature=0.0,  # Low temperature for consistent evaluation
            max_tokens=10     # Only need one word response
        )

        judgment = judge_response.choices[0].message.content.strip().upper()
        
        # Log the judgment
        print(f"\n⚖️ LLM Judge evaluation: {judgment}")
        
        return judgment == "RELEVANT"

    except Exception as e:
        print(f"❌ Error in LLM judge evaluation: {e}")
        # Default to True if judge fails (don't break the pipeline)
        return True


def get_fallback_response(original_query):
    """
    Returns a helpful fallback response when the main response is deemed irrelevant
    """
    return f"""Sorry, I couldn't find sufficient relevant information to answer your query: "{original_query}"

Please try:
• Rephrasing your question with different keywords
• Being more specific about what you're looking for
• Checking if your question relates to the content in the uploaded document

If you believe this document should contain the information you're seeking, try asking about related topics or broader concepts that might be present in the document."""


def evaluate_and_filter_response(original_query, generated_response, context_used):
    """
    Main function that evaluates response and returns either the original response 
    or a fallback message if irrelevant
    """
    is_relevant = evaluate_response_relevance(original_query, generated_response, context_used)
    
    if is_relevant:
        print("✅ Response passed relevance check")
        return generated_response
    else:
        print("❌ Response failed relevance check - returning fallback")
        return get_fallback_response(original_query)