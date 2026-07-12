"""Task decomposition: breaks a broad research topic into distinct subtopics.

Uses a single Claude Agent SDK `query()` call with structured JSON output
(`output_format`) so the result is a reliably parseable list of subtopics rather
than free text we have to scrape.
"""
from __future__ import annotations

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

from .models import Subtopic

DECOMPOSITION_SCHEMA = {
    "type": "object",
    "properties": {
        "subtopics": {
            "type": "array",
            "minItems": 5,
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "short kebab-case slug, e.g. 'economic-impact'",
                    },
                    "title": {"type": "string"},
                    "rationale": {
                        "type": "string",
                        "description": "why this subtopic matters to covering the full topic",
                    },
                },
                "required": ["id", "title", "rationale"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["subtopics"],
    "additionalProperties": False,
}

DECOMPOSITION_SYSTEM_PROMPT = (
    "You are a research planning specialist. Given a broad research topic, decompose "
    "it into at least 5 distinct, non-overlapping subtopics that together cover the "
    "full breadth of the subject (for example: historical/background, "
    "technical/mechanistic, economic, social/ethical, current state, future outlook, "
    "or comparative/regional angles — whichever are actually relevant to this topic). "
    "Each subtopic must be specific enough to be independently researched via web "
    "search, and distinct enough that its findings won't just duplicate another "
    "subtopic's. Do not produce subtopics that are just reworded synonyms of the "
    "overall topic or of each other."
)


async def decompose_topic(
    topic: str,
    *,
    min_subtopics: int = 5,
    model: str | None = None,
) -> list[Subtopic]:
    """Ask an LLM to break `topic` into at least `min_subtopics` distinct subtopics."""
    options = ClaudeAgentOptions(
        system_prompt=DECOMPOSITION_SYSTEM_PROMPT,
        tools=[],
        allowed_tools=[],
        permission_mode="bypassPermissions",
        model=model,
        max_turns=1,
        output_format={"type": "json_schema", "schema": DECOMPOSITION_SCHEMA},
    )

    prompt = (
        f"Research topic: {topic!r}\n\n"
        f"Produce at least {min_subtopics} subtopics as instructed."
    )

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            if message.subtype != "success" or not message.structured_output:
                raise RuntimeError(
                    f"Topic decomposition failed (subtype={message.subtype!r})"
                )
            raw_subtopics = message.structured_output["subtopics"]
            subtopics = [Subtopic(**item) for item in raw_subtopics]
            if len(subtopics) < min_subtopics:
                raise RuntimeError(
                    f"Decomposition returned only {len(subtopics)} subtopics; "
                    f"need >= {min_subtopics}"
                )
            return subtopics

    raise RuntimeError("Topic decomposition produced no result message")
