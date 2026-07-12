"""Shared data structures for the research coordinator."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

CoverageStatus = Literal["sufficient", "superficial", "empty"]


@dataclass
class Subtopic:
    id: str
    title: str
    rationale: str


@dataclass
class SubtopicFindings:
    subtopic_id: str
    subtopic_title: str
    summary: str
    key_findings: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    queries_used: list[str] = field(default_factory=list)


@dataclass
class CoverageAssessment:
    subtopic_id: str
    subtopic_title: str
    status: CoverageStatus
    reasons: list[str] = field(default_factory=list)


@dataclass
class CoverageReport:
    assessments: list[CoverageAssessment]
    sufficient_count: int
    gap_count: int

    @property
    def is_complete(self) -> bool:
        return self.gap_count == 0

    def gaps(self) -> list[CoverageAssessment]:
        return [a for a in self.assessments if a.status != "sufficient"]
