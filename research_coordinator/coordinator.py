"""Coordinator agent.

Orchestrates the full pipeline:
  1. Decompose the broad topic into >= N distinct subtopics (LLM call).
  2. Spawn one web-search subagent per subtopic, in parallel.
  3. Aggregate results and evaluate coverage completeness.
  4. If any subtopic has no findings or only superficial coverage, generate
     targeted follow-up queries and re-delegate to that subtopic's subagent.
     Repeat until coverage is sufficient or a max-iteration safety cap is hit.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from .coverage import evaluate_coverage
from .decomposition import decompose_topic
from .models import CoverageAssessment, CoverageReport, Subtopic, SubtopicFindings
from .refinement import generate_targeted_queries
from .subagents import run_subagent_research

logger = logging.getLogger("research_coordinator")


@dataclass
class ResearchReport:
    topic: str
    subtopics: list[Subtopic]
    findings: dict[str, SubtopicFindings]
    coverage: CoverageReport
    iterations_used: int


def _merge_findings(prior: SubtopicFindings, new: SubtopicFindings) -> SubtopicFindings:
    """Combine a refinement pass's findings with what was already gathered.

    De-duplicates rather than discarding prior work, so re-delegation only adds
    to the picture instead of replacing it.
    """
    merged_findings = prior.key_findings + [
        f for f in new.key_findings if f not in prior.key_findings
    ]
    merged_sources = prior.sources + [s for s in new.sources if s not in prior.sources]

    # Only fold the new pass's narrative into history if it actually
    # contributed findings or sources. Otherwise a failed/empty refinement
    # pass (e.g. "subagent failed; no findings recovered") would permanently
    # poison the merged summary with failure text, even after a later pass
    # succeeds — which previously caused evaluate_coverage's text-pattern
    # check to misclassify subtopics with substantial findings as "empty".
    merged_summary = prior.summary
    if new.summary and (new.key_findings or new.sources):
        merged_summary = (
            f"{prior.summary}\n\nRefinement pass: {new.summary}".strip()
            if prior.summary
            else new.summary
        )

    return SubtopicFindings(
        subtopic_id=prior.subtopic_id,
        subtopic_title=prior.subtopic_title,
        summary=merged_summary,
        key_findings=merged_findings,
        sources=merged_sources,
        queries_used=prior.queries_used + new.queries_used,
    )


class ResearchCoordinator:
    """Runs the decompose -> fan-out -> evaluate -> refine loop for one topic."""

    def __init__(
        self,
        *,
        min_subtopics: int = 3,
        max_refinement_iterations: int = 1,
        planning_model: str | None = None,
        subagent_model: str | None = None,
    ) -> None:
        self.min_subtopics = min_subtopics
        self.max_refinement_iterations = max_refinement_iterations
        self.planning_model = planning_model
        self.subagent_model = subagent_model

    async def run(self, topic: str) -> ResearchReport:
        logger.info("Decomposing topic: %s", topic)
        subtopics = await decompose_topic(
            topic, min_subtopics=self.min_subtopics, model=self.planning_model
        )
        logger.info(
            "Decomposed into %d subtopics: %s",
            len(subtopics),
            [s.title for s in subtopics],
        )

        # Spawn exactly one web-search subagent per subtopic, concurrently.
        initial_findings = await asyncio.gather(
            *(
                run_subagent_research(subtopic, model=self.subagent_model)
                for subtopic in subtopics
            )
        )
        findings: dict[str, SubtopicFindings] = {
            f.subtopic_id: f for f in initial_findings
        }

        coverage = evaluate_coverage(list(findings.values()))
        iteration = 0

        while not coverage.is_complete and iteration < self.max_refinement_iterations:
            iteration += 1
            gaps = coverage.gaps()
            logger.info(
                "Iteration %d: %d subtopic(s) need refinement: %s",
                iteration,
                len(gaps),
                [g.subtopic_title for g in gaps],
            )

            subtopics_by_id = {s.id: s for s in subtopics}
            refined = await asyncio.gather(
                *(self._refine_one(g, subtopics_by_id, findings) for g in gaps)
            )
            for f in refined:
                findings[f.subtopic_id] = f

            coverage = evaluate_coverage(list(findings.values()))

        if not coverage.is_complete:
            logger.warning(
                "Reached max refinement iterations (%d) with unresolved gaps: %s",
                self.max_refinement_iterations,
                [g.subtopic_title for g in coverage.gaps()],
            )

        return ResearchReport(
            topic=topic,
            subtopics=subtopics,
            findings=findings,
            coverage=coverage,
            iterations_used=iteration,
        )

    async def _refine_one(
        self,
        assessment: CoverageAssessment,
        subtopics_by_id: dict[str, Subtopic],
        findings: dict[str, SubtopicFindings],
    ) -> SubtopicFindings:
        subtopic = subtopics_by_id[assessment.subtopic_id]
        prior = findings[assessment.subtopic_id]

        targeted_queries = await generate_targeted_queries(
            prior, assessment, model=self.planning_model
        )
        new_findings = await run_subagent_research(
            subtopic,
            targeted_queries=targeted_queries,
            model=self.subagent_model,
        )
        return _merge_findings(prior, new_findings)
