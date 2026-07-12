"""Web-search subagents.

Each subagent is an independent Claude Agent SDK `query()` session, restricted to
the `WebSearch` tool, that researches exactly one subtopic. Subtopic context is
injected via the system prompt (what to research and why it matters) and, on
refinement passes, via specific targeted queries to run.

We deliberately don't use the SDK's `agents=`/`AgentDefinition` mechanism for this
fan-out: that mechanism lets the *orchestrator LLM* decide when to delegate via the
built-in Agent tool, which is nondeterministic. Here the coordinator needs to
guarantee exactly one subagent per identified subtopic and control re-delegation
itself, so each subagent is spawned directly as its own `query()` call and run
concurrently via asyncio.
"""
from __future__ import annotations

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

from .models import Subtopic, SubtopicFindings

FINDINGS_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "key_findings": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Distinct, specific facts/figures/claims found — not restatements of the same point.",
        },
        "sources": {
            "type": "array",
            "items": {"type": "string"},
            "description": "URLs or named publications the findings are drawn from.",
        },
    },
    "required": ["summary", "key_findings", "sources"],
    "additionalProperties": False,
}

SUBAGENT_SYSTEM_PROMPT_TEMPLATE = (
    "You are a focused web-research subagent. Your ONLY job is to research the "
    "subtopic below thoroughly using the WebSearch tool, then report substantive, "
    "specific findings: concrete facts, figures, named sources, and dates — not "
    "vague generalities. Run multiple distinct searches covering different angles "
    "before answering. If you genuinely cannot find relevant information after "
    "searching, say so explicitly in the summary rather than fabricating content.\n\n"
    "Subtopic: {title}\n"
    "Why this subtopic matters: {rationale}\n"
)


def _build_prompt(subtopic: Subtopic, targeted_queries: list[str] | None) -> str:
    if not targeted_queries:
        return (
            f"Research the subtopic '{subtopic.title}' broadly. Run several distinct "
            f"WebSearch queries covering different angles of this subtopic, then "
            f"synthesize what you found into the required structured output."
        )
    queries_block = "\n".join(f"- {q}" for q in targeted_queries)
    return (
        f"A previous research pass on '{subtopic.title}' was flagged as incomplete "
        f"or superficial. Run WebSearch specifically for these targeted follow-up "
        f"queries (and natural variations of them), then report what you find:\n"
        f"{queries_block}\n\n"
        f"Focus on filling these specific gaps — do not just repeat generic "
        f"background information already likely to be known."
    )


async def run_subagent_research(
    subtopic: Subtopic,
    *,
    targeted_queries: list[str] | None = None,
    model: str | None = None,
    max_turns: int = 6,
) -> SubtopicFindings:
    """Spawn one web-search subagent to research `subtopic` and return its findings.

    When `targeted_queries` is provided (a refinement pass), the subagent is
    instructed to focus specifically on closing those gaps instead of doing a
    broad initial search.
    """
    options = ClaudeAgentOptions(
        system_prompt=SUBAGENT_SYSTEM_PROMPT_TEMPLATE.format(
            title=subtopic.title, rationale=subtopic.rationale
        ),
        tools=["WebSearch"],
        allowed_tools=["WebSearch"],
        permission_mode="bypassPermissions",
        model=model,
        max_turns=max_turns,
        output_format={"type": "json_schema", "schema": FINDINGS_SCHEMA},
    )

    prompt = _build_prompt(subtopic, targeted_queries)

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            if message.subtype != "success" or not message.structured_output:
                return SubtopicFindings(
                    subtopic_id=subtopic.id,
                    subtopic_title=subtopic.title,
                    summary=f"Subagent failed (subtype={message.subtype!r}); no findings recovered.",
                    queries_used=targeted_queries or [],
                )
            data = message.structured_output
            return SubtopicFindings(
                subtopic_id=subtopic.id,
                subtopic_title=subtopic.title,
                summary=data.get("summary", ""),
                key_findings=data.get("key_findings", []),
                sources=data.get("sources", []),
                queries_used=targeted_queries or [],
            )

    return SubtopicFindings(
        subtopic_id=subtopic.id,
        subtopic_title=subtopic.title,
        summary="Subagent produced no result message.",
        queries_used=targeted_queries or [],
    )
