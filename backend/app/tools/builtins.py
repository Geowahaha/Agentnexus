import ast
import operator
import re
from collections import Counter
from datetime import datetime, timezone

import httpx
from langchain_core.tools import tool

_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _eval_math(expression: str) -> float:
    node = ast.parse(expression, mode="eval").body

    def _evaluate(item):
        if isinstance(item, ast.Constant) and isinstance(item.value, (int, float)):
            return item.value
        if isinstance(item, ast.UnaryOp) and isinstance(item.op, ast.USub):
            return _SAFE_OPERATORS[ast.USub](_evaluate(item.operand))
        if isinstance(item, ast.BinOp) and type(item.op) in _SAFE_OPERATORS:
            return _SAFE_OPERATORS[type(item.op)](_evaluate(item.left), _evaluate(item.right))
        raise ValueError("Unsupported expression")

    return float(_evaluate(node))


@tool
def calculator(expression: str) -> str:
    """Evaluate a basic math expression. Supports +, -, *, /, parentheses, and powers."""
    try:
        return str(_eval_math(expression))
    except Exception as exc:
        return f"Calculator error: {exc}"


@tool
def current_datetime() -> str:
    """Return the current UTC date and time."""
    return datetime.now(timezone.utc).isoformat()


@tool
def word_count(text: str) -> str:
    """Count words and characters in the provided text."""
    words = re.findall(r"\b\w+\b", text)
    return f"words={len(words)}, characters={len(text)}"


@tool
def keyword_extract(text: str, limit: int = 10) -> str:
    """Extract top keywords from text, useful for SEO and research tasks."""
    tokens = re.findall(r"[a-zA-Z]{3,}", text.lower())
    stopwords = {
        "the", "and", "for", "with", "that", "this", "from", "your", "you", "are", "was", "have",
    }
    filtered = [token for token in tokens if token not in stopwords]
    ranked = Counter(filtered).most_common(max(limit, 1))
    if not ranked:
        return "No keywords found."
    return ", ".join(f"{word} ({count})" for word, count in ranked)


@tool
async def web_search(query: str) -> str:
    """Search the web for facts and context related to a query."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_redirect": 1, "no_html": 1},
            )
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:
        return f"Web search unavailable: {exc}"

    abstract = payload.get("AbstractText") or ""
    heading = payload.get("Heading") or ""
    related = [item.get("Text", "") for item in payload.get("RelatedTopics", []) if isinstance(item, dict)]
    related = [item for item in related if item][:5]

    if not abstract and not related:
        return f"No web results found for '{query}'."

    parts = [f"Query: {query}"]
    if heading:
        parts.append(f"Heading: {heading}")
    if abstract:
        parts.append(f"Summary: {abstract}")
    if related:
        parts.append("Related: " + " | ".join(related))
    return "\n".join(parts)