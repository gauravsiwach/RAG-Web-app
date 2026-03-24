"""
query_translation.py

Handles all query translation strategies BEFORE vector search.
Three strategies improve retrieval coverage:
  1. Multi-Query     – expand one query into multiple phrasings
  2. Step-Back       – generate a broader, more abstract version of the query
  3. Sub-Query       – decompose a complex query into simpler sub-questions
"""

from openai import OpenAI

client = OpenAI()

def translate_query(query: str) -> list[str]:
    """
    Orchestrates all 3 query translation strategies and returns a combined
    deduplicated list of queries to run against the vector DB.
    """
    all_queries = set()

    # Strategy 1: Multi-Query – different phrasings of the same question
    multi = generate_multi_queries(query)
    all_queries.update(multi)

    # Strategy 2: Step-Back – broader, abstract version of the question
    # step_back = generate_step_back_query(query)
    # all_queries.add(step_back)

    # # Strategy 3: Sub-Queries – decompose complex question into simpler ones
    # sub = generate_sub_queries(query)
    # all_queries.update(sub)

    final_queries = list(all_queries)
    print(f"\n📋 Total translated queries: {len(final_queries)}")
    return final_queries

def generate_multi_queries(query: str) -> list[str]:
    """
    Multi-Query Translation:
    Rewrites the original query into 3 different phrasings.
    This helps capture more relevant chunks by covering different wording.
    e.g. "What is JSX?" → ["Explain JSX in React", "How does JSX work?", "JSX syntax overview"]
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert at query rewriting for document retrieval. "
                    "Given a user question, generate 3 different phrasings of the same question "
                    "to maximize retrieval coverage. Return only the questions, one per line, no numbering."
                )
            },
            {"role": "user", "content": f"Original query: {query}"}
        ]
    )
    lines = response.choices[0].message.content.strip().split("\n")
    # Include the original + generated queries, filter empty lines
    all_queries = [query] + [line.strip() for line in lines if line.strip()]
    print(f"🔀 Multi-queries generated: {all_queries}")
    return all_queries


def generate_step_back_query(query: str) -> str:
    """
    Step-Back Prompting:
    Generates a broader, more abstract version of the query.
    Helps retrieve higher-level context that might not match the specific query.
    e.g. "What does the useState hook return?" → "How do React hooks work?"
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert at query abstraction. "
                    "Given a specific question, generate a broader, more general version "
                    "that captures the high-level topic. Return only the abstracted question."
                )
            },
            {"role": "user", "content": f"Specific query: {query}"}
        ]
    )
    step_back = response.choices[0].message.content.strip()
    print(f"⬆️  Step-back query: {step_back}")
    return step_back


def generate_sub_queries(query: str) -> list[str]:
    """
    Sub-Query Decomposition:
    Breaks a complex query into smaller, focused sub-questions.
    Useful when the original query has multiple parts or concepts.
    e.g. "What is JSX and how is it different from HTML?" → ["What is JSX?", "How is JSX different from HTML?"]
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert at query decomposition. "
                    "Break the given question into 2-3 simple, focused sub-questions "
                    "that together cover the full original question. "
                    "Return only the sub-questions, one per line, no numbering."
                )
            },
            {"role": "user", "content": f"Complex query: {query}"}
        ]
    )
    lines = response.choices[0].message.content.strip().split("\n")
    sub_queries = [line.strip() for line in lines if line.strip()]
    print(f"🔪 Sub-queries generated: {sub_queries}")
    return sub_queries