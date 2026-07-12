"""Aggregation + coverage-completeness evaluation.

Plain, deterministic Python — no extra LLM call needed to decide whether a
subtopic's findings are substantive. This keeps evaluation fast, cheap, and
easy to unit test, and gives the coordinator a clear, inspectable reason for
every re-delegation decision.
"""
from __future__ import annotations

from .models import CoverageAssessment, CoverageReport, SubtopicFindings

MIN_SUMMARY_CHARS = 120
MIN_KEY_FINDINGS = 3
MIN_SOURCES = 2

_EMPTY_MARKERS = (
    "no relevant information",
    "could not find",
    "couldn't find",
    "no results found",
    "unable to find",
    "no findings",
    "failed to find",
    "subagent failed",
    "no result message",
)


def evaluate_coverage(results: list[SubtopicFindings]) -> CoverageReport:
    """Aggregate subagent findings and flag subtopics with no findings or
    superficial coverage.

    Status per subtopic:
      - "empty":       no key findings AND no sources, or the summary reads like
                        an explicit non-finding (e.g. "no relevant information...").
      - "superficial": has some content but falls short of the substantive-
                        coverage thresholds (too few distinct findings, too few
                        sources, or too short a summary).
      - "sufficient":  otherwise.
    """
    assessments: list[CoverageAssessment] = []

    for r in results:
        reasons: list[str] = []
        summary_lower = r.summary.strip().lower()

        has_no_findings = len(r.key_findings) == 0
        has_no_sources = len(r.sources) == 0
        # Text-pattern matching must never override structured evidence: a
        # merged summary can carry forward "couldn't find X" phrasing from an
        # earlier failed refinement pass even after a later pass succeeds, so
        # only trust the marker when there's also no structured finding data.
        is_explicit_empty = has_no_findings and any(
            marker in summary_lower for marker in _EMPTY_MARKERS
        )

        if has_no_findings and has_no_sources:
            reasons.append("no substantive findings returned")
            status = "empty"
        elif is_explicit_empty:
            reasons.append("summary indicates no relevant information was located")
            status = "empty"
        else:
            if len(r.key_findings) < MIN_KEY_FINDINGS:
                reasons.append(
                    f"only {len(r.key_findings)} distinct finding(s) "
                    f"(need >= {MIN_KEY_FINDINGS})"
                )
            if len(r.sources) < MIN_SOURCES:
                reasons.append(
                    f"only {len(r.sources)} source(s) (need >= {MIN_SOURCES})"
                )
            if len(r.summary.strip()) < MIN_SUMMARY_CHARS:
                reasons.append("summary too short to be substantive")

            status = "superficial" if reasons else "sufficient"

        assessments.append(
            CoverageAssessment(
                subtopic_id=r.subtopic_id,
                subtopic_title=r.subtopic_title,
                status=status,
                reasons=reasons,
            )
        )

    gap_count = sum(1 for a in assessments if a.status != "sufficient")
    return CoverageReport(
        assessments=assessments,
        sufficient_count=len(assessments) - gap_count,
        gap_count=gap_count,
    )
