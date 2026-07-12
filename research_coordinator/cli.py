"""Command-line entry point for the research coordinator.

Usage:
    python -m research_coordinator "The future of nuclear fusion energy"
    python -m research_coordinator "Topic" --min-subtopics 6 --max-iterations 2 \\
        --planning-model sonnet --subagent-model haiku --verbose
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
from pathlib import Path

from .coordinator import ResearchCoordinator, ResearchReport
from .models import CoverageReport


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader (only sets vars not already present in the environment).

    The Claude Agent SDK reads ANTHROPIC_API_KEY from the process environment and
    does not load .env files itself, so this fills that gap without requiring
    python-dotenv as a hard dependency.
    """
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _print_report(report: ResearchReport) -> None:
    coverage: CoverageReport = report.coverage
    print(f"\n{'=' * 80}\nRESEARCH REPORT: {report.topic}\n{'=' * 80}\n")
    print(
        f"Coverage: {coverage.sufficient_count}/{len(report.subtopics)} subtopics "
        f"sufficient after {report.iterations_used} refinement iteration(s)\n"
    )
    for subtopic in report.subtopics:
        finding = report.findings[subtopic.id]
        assessment = next(
            a for a in coverage.assessments if a.subtopic_id == subtopic.id
        )
        print(f"--- {subtopic.title} [{assessment.status.upper()}] ---")
        if assessment.reasons:
            print(f"  (remaining gaps: {'; '.join(assessment.reasons)})")
        print(f"  {finding.summary}\n")
        for kf in finding.key_findings:
            print(f"  - {kf}")
        if finding.sources:
            print("  Sources:")
            for s in finding.sources:
                print(f"    * {s}")
        print()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Multi-agent research coordinator")
    parser.add_argument("topic", help="Broad research topic to investigate")
    parser.add_argument(
        "--min-subtopics", type=int, default=3, help="Minimum subtopics to decompose into"
    )
    parser.add_argument(
        "--max-iterations", type=int, default=1, help="Max refinement loop iterations"
    )
    parser.add_argument(
        "--planning-model",
        default=None,
        help="Model for decomposition/refinement calls (e.g. 'sonnet'); defaults to the SDK default",
    )
    parser.add_argument(
        "--subagent-model",
        default=None,
        help="Model for web-search subagents (e.g. 'haiku' for cost control); defaults to the SDK default",
    )
    parser.add_argument("--verbose", action="store_true", help="Log progress to stderr")
    return parser.parse_args()


async def _run(args: argparse.Namespace) -> ResearchReport:
    coordinator = ResearchCoordinator(
        min_subtopics=args.min_subtopics,
        max_refinement_iterations=args.max_iterations,
        planning_model=args.planning_model,
        subagent_model=args.subagent_model,
    )
    return await coordinator.run(args.topic)


def main() -> None:
    _load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    args = _parse_args()
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    report = asyncio.run(_run(args))
    _print_report(report)


if __name__ == "__main__":
    main()
