"""Natural-language search via Claude tool_use.

User types a sentence ("find payable trading agents with at least 5 reviewers").
Claude returns a structured filter dict that we hand to q_agent_search().
Cheap: one Haiku call per query.

Key resolution order:
  1. st.secrets["anthropic"]["api_key"]
  2. environ ANTHROPIC_API_KEY
  3. None → caller renders a hint and skips the call
"""
from __future__ import annotations

import os
from typing import Any

try:
    import streamlit as st
    _HAS_STREAMLIT = True
except ImportError:
    _HAS_STREAMLIT = False

try:
    import anthropic
    _HAS_ANTHROPIC = True
except ImportError:
    _HAS_ANTHROPIC = False


SEARCH_TOOL = {
    "name": "filter_agents",
    "description": (
        "Filter ERC-8004 agents in the BigQuery dataset by structured criteria. "
        "Leave any field unset when the user didn't mention it. Owner addresses "
        "must be 42-char hex like 0xabc…. Scores are 0-100."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "agent_id": {
                "type": "integer",
                "description": "Exact agent_id when the user gives one.",
            },
            "owner": {
                "type": "string",
                "description": "Owner wallet address (0x… 42 chars).",
            },
            "name_contains": {
                "type": "string",
                "description": "Case-insensitive substring of the agent name field.",
            },
            "description_contains": {
                "type": "string",
                "description": "Case-insensitive substring of the description field.",
            },
            "min_unique_clients": {
                "type": "integer",
                "description": "Minimum number of distinct reviewers. Default to 3 if the user says 'trustworthy' / 'real' / 'verified'.",
            },
            "min_avg_score": {
                "type": "number",
                "description": "Minimum average reputation score, 0-100. Default to 80 if the user says 'high reputation' / 'top'.",
            },
            "x402_only": {
                "type": "boolean",
                "description": "Restrict to cards claiming x402Support=true (payable agents).",
            },
            "has_services": {
                "type": "boolean",
                "description": "Restrict to cards with a non-empty services[] array (functional agents).",
            },
            "limit": {
                "type": "integer",
                "description": "Max rows to return. Default 50.",
            },
        },
    },
}

SYSTEM_PROMPT = (
    "You are an agent-search assistant for an ERC-8004 explorer dashboard. "
    "The user asks for agents in natural language; you call the `filter_agents` "
    "tool exactly once with the smallest set of fields needed. "
    "Do not invent filters the user didn't ask for. "
    "If the user says 'payable' set x402_only=true. "
    "If they say 'trustworthy' / 'reputable' set min_unique_clients to at least 3. "
    "If they say 'functional' / 'has endpoint' set has_services=true. "
    "Substring filters are case-insensitive — pass them lowercase."
)


def _get_api_key() -> str | None:
    if _HAS_STREAMLIT:
        try:
            key = st.secrets.get("anthropic", {}).get("api_key")
            if key:
                return key
        except Exception:
            pass
    return os.environ.get("ANTHROPIC_API_KEY")


def available() -> bool:
    return _HAS_ANTHROPIC and _get_api_key() is not None


def parse_query(user_text: str) -> dict[str, Any] | None:
    """Turn user_text into a filter dict via one Haiku call.
    Returns None if the API key is missing or the model didn't call the tool."""
    if not available():
        return None

    client = anthropic.Anthropic(api_key=_get_api_key())
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        tools=[SEARCH_TOOL],
        tool_choice={"type": "tool", "name": "filter_agents"},
        messages=[{"role": "user", "content": user_text}],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == "filter_agents":
            return dict(block.input)
    return None
