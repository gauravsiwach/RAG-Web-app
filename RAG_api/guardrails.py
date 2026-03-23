"""
guardrails.py

Central guardrail layer for the RAG chatbot.
All chat handlers (pdf, web, json v1, json v2) call this module
at input (before any LLM/vector calls) and at output (before returning to user).

INPUT  guardrails: fast, no LLM calls — reject bad queries early.
OUTPUT guardrails: LLM-based — absorbs and replaces response_judge.py.
"""

import re
from openai import OpenAI

client = OpenAI()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MAX_QUERY_LENGTH = 2000  # characters

# Known prompt injection patterns (case-insensitive)
_INJECTION_PATTERNS = [
    r"ignore (previous|all|above|prior) instructions?",
    r"disregard (previous|all|above|prior) instructions?",
    r"forget (everything|all|previous|your instructions?)",
    r"you are now",
    r"act as (a |an )?(different|new|another|evil|unrestricted)",
    r"pretend (you are|to be)",
    r"new (role|persona|instructions?|task)",
    r"system\s*:\s*(you|ignore|forget)",
    r"jailbreak",
    r"dan mode",
    r"developer mode",
    r"override (safety|guidelines|restrictions?|rules?)",
]
_INJECTION_REGEX = re.compile(
    "|".join(_INJECTION_PATTERNS), re.IGNORECASE
)

# ---------------------------------------------------------------------------
# INPUT guardrails
# ---------------------------------------------------------------------------

def guardrails_input(query: str) -> dict:
    """
    Run all input guardrails against the user query.

    Returns:
        {"passed": True}  — query is clean, proceed with pipeline
        {"passed": False, "message": str}  — reject, return message to user
    """
    # 1. Empty / whitespace check
    if not query or not query.strip():
        print("🛡️ [Guardrail] Blocked: empty query")
        return {
            "passed": False,
            "message": "Please enter a question before sending."
        }

    # 2. Max length check
    if len(query) > MAX_QUERY_LENGTH:
        print(f"🛡️ [Guardrail] Blocked: query too long ({len(query)} chars)")
        return {
            "passed": False,
            "message": f"Your query is too long ({len(query)} characters). Please keep it under {MAX_QUERY_LENGTH} characters."
        }

    # 3. Prompt injection detection (regex — no LLM cost)
    if _INJECTION_REGEX.search(query):
        print(f"🛡️ [Guardrail] Blocked: prompt injection attempt detected")
        return {
            "passed": False,
            "message": "I can only answer questions about the uploaded content. Please ask a relevant question."
        }

    print(f"✅ [Guardrail] Input passed all checks (len={len(query.strip())})")
    return {"passed": True}


# ---------------------------------------------------------------------------
# OUTPUT guardrails
# ---------------------------------------------------------------------------

def guardrails_output(original_query: str, generated_response: str, context_used: str) -> str:
    """
    Run output guardrails on the LLM response.

    - Relevance check: is the answer actually addressing the query?
    - Falls back to a helpful message if irrelevant.

    Absorbs and replaces response_judge.evaluate_and_filter_response().

    Returns:
        The original response (if passes) or a fallback message (if fails).
    """
    if _is_response_relevant(original_query, generated_response, context_used):
        print("✅ [Guardrail] Output passed relevance check")
        return generated_response

    print("🛡️ [Guardrail] Output failed relevance check — returning fallback")
    return _fallback_response(original_query)


def _is_response_relevant(original_query: str, generated_response: str, context_used: str) -> bool:
    """LLM-as-Judge: returns True if response is relevant to the query."""
    try:
        JUDGE_SYSTEM_PROMPT = """
You are an AI judge evaluating whether an AI assistant's response adequately answers
the user's query based on the provided context.

Evaluation criteria:
1. Does the response directly address the user's question?
2. Is the response grounded in the provided context?
3. Does the response provide specific, useful information?

Respond with ONLY one word: RELEVANT or IRRELEVANT.
Be strict — generic or vague responses that don't address the question are IRRELEVANT.
"""
        JUDGE_USER_PROMPT = f"""
Original User Query: "{original_query}"

AI Assistant's Response: "{generated_response}"

Context Used: "{context_used[:1500]}"

Is the response relevant to the query?
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": JUDGE_USER_PROMPT},
            ],
            temperature=0.0,
            max_tokens=10,
        )
        judgment = response.choices[0].message.content.strip().upper()
        print(f"\n⚖️ [Guardrail] LLM Judge: {judgment}")
        return judgment == "RELEVANT"

    except Exception as e:
        # If judge errors, default to passing (don't break the pipeline)
        print(f"⚠️ [Guardrail] Judge failed ({e}), defaulting to RELEVANT")
        return True


def _fallback_response(original_query: str) -> str:
    return (
        f'Sorry, I couldn\'t find sufficient relevant information to answer: "{original_query}"\n\n'
        "Please try:\n"
        "• Rephrasing your question with different keywords\n"
        "• Being more specific about what you're looking for\n"
        "• Ensuring your question relates to the uploaded content"
    )
