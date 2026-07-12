"""Generates targeted follow-up search queries for subtopics with coverage gaps.

Used by the coordinator's refinement loop: when `coverage.evaluate_coverage`
flags a subtopic as "empty" or "superficial", this turns that gap into concrete,
re-runnable WebSearch queries instead of just re-asking the same broad question.
"""
from __future__ import annotations

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

from .models import CoverageAssessment, SubtopicFindings

QUERIES_SCHEMA = {
    "type": "object",
    "properties": {
        "queries": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 2,
            "maxItems": 5,
        }
    },
    "required": ["queries"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = (
    "You are a search-strategy specialist. Given a subtopic, what was already "
    "found, and why the coverage was judged insufficient, propose 2-5 specific, "
    "targeted web search queries that would plausibly surface the missing "
    "information. Queries must be concrete search strings a person could type "
    "into a search engine — not vague restatements of the subtopic."
)


async def generate_targeted_queries(
    finding: SubtopicFindings,
    assessment: CoverageAssessment,
    *,
    model: str | None = None,
) -> list[str]:
    prior_findings = "\n".join(f"- {f}" for f in finding.key_findings) or "(none)"
    gap_reasons = "; ".join(assessment.reasons) or "no findings at all"

    prompt = (
        f"Subtopic: {finding.subtopic_title}\n"
        f"Findings so far:\n{prior_findings}\n\n"
        f"Coverage gap reasons: {gap_reasons}\n\n"
        f"Propose targeted search queries to close these gaps."
    )

    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        tools=[],
        allowed_tools=[],
        permission_mode="bypassPermissions",
        model=model,
        max_turns=1,
        output_format={"type": "json_schema", "schema": QUERIES_SCHEMA},
    )

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            if message.subtype == "success" and message.structured_output:
                queries = message.structured_output.get("queries", [])
                if queries:
                    return queries
            break

    # Fallback if the planning call fails for any reason — keep the refinement
    # loop moving rather than stalling on a single subagent's failure.
    return [f"{finding.subtopic_title} detailed statistics and recent developments"]
