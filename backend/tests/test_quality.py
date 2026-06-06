from models.schemas import ResearchReport, ResearchTask, Source
from utils.quality import evaluate_report_quality


def test_evaluate_report_quality_scores_sources_and_citations():
    report = ResearchReport(
        id="r1",
        topic="AI internship market",
        markdown_content="Finding from source [1]. Another claim [2].",
        tasks=[
            ResearchTask(
                id="t1",
                subtopic="Hiring demand",
                summary="AI internship demand is growing [1].",
                status="complete",
                sources=[
                    Source(url="https://example.com/a", title="A"),
                    Source(url="https://news.example.org/b", title="B"),
                ],
            ),
            ResearchTask(
                id="t2",
                subtopic="Skill expectations",
                summary="Employers expect Python and cloud skills [1].",
                status="complete",
                sources=[
                    Source(url="https://example.com/c", title="C"),
                    Source(url="https://jobs.example.net/d", title="D"),
                ],
            ),
        ],
    )

    quality = evaluate_report_quality(report)

    assert quality.source_count == 4
    assert quality.unique_domain_count == 3
    assert quality.citation_count >= 4
    assert quality.citation_coverage == 1.0
    assert quality.success_rate == 1.0
    assert quality.confidence_score >= 90
    assert quality.warnings == []


def test_evaluate_report_quality_warns_on_thin_sources():
    report = ResearchReport(
        id="r2",
        topic="Thin report",
        tasks=[
            ResearchTask(
                id="t1",
                subtopic="Only track",
                summary="Summary without citations.",
                status="complete",
                sources=[Source(url="https://example.com/a", title="A")],
            ),
            ResearchTask(
                id="t2",
                subtopic="Failed track",
                summary="Search failed",
                status="failed",
                sources=[],
            ),
        ],
    )

    quality = evaluate_report_quality(report)

    assert quality.source_count == 1
    assert quality.citation_coverage == 0
    assert quality.success_rate == 0.5
    assert quality.warnings
