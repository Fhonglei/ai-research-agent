import re
from urllib.parse import urlparse

from models.schemas import ResearchQuality, ResearchReport, ResearchTask


_CITATION_RE = re.compile(r"\[(\d{1,3})\]")


def evaluate_report_quality(report: ResearchReport) -> ResearchQuality:
    """Compute lightweight quality signals for a generated research report."""
    tasks = report.tasks or []
    completed = [task for task in tasks if task.status == "complete"]
    failed = [task for task in tasks if task.status == "failed"]

    source_urls = [
        source.url.strip()
        for task in tasks
        for source in task.sources
        if source.url and source.url.strip()
    ]
    unique_source_urls = sorted(set(source_urls))
    domains = {
        urlparse(url).netloc.lower().removeprefix("www.")
        for url in unique_source_urls
        if urlparse(url).netloc
    }

    citation_text = "\n".join(
        [report.markdown_content or ""]
        + [task.summary or "" for task in completed]
    )
    citation_count = len(_CITATION_RE.findall(citation_text))

    cited_tasks = [
        task for task in completed
        if _CITATION_RE.search(task.summary or "")
    ]
    citation_coverage = _ratio(len(cited_tasks), len(completed))
    success_rate = _ratio(len(completed), len(tasks))

    expected_sources = max(len(completed) * 2, 1)
    source_score = min(len(unique_source_urls) / expected_sources, 1.0)
    domain_score = min(len(domains) / max(len(completed), 1), 1.0)
    confidence_score = round(
        100 * (
            source_score * 0.35
            + citation_coverage * 0.25
            + success_rate * 0.25
            + domain_score * 0.15
        ),
        1,
    )

    warnings: list[str] = []
    if not completed:
        warnings.append("No research tracks completed successfully.")
    if len(unique_source_urls) < max(len(completed) * 2, 2):
        warnings.append("Source coverage is thin; add more independent sources.")
    if citation_coverage < 0.7 and completed:
        warnings.append("Many summaries do not include inline citations.")
    if len(domains) < max(min(len(completed), 3), 1) and completed:
        warnings.append("Sources come from too few unique domains.")
    if failed:
        warnings.append(f"{len(failed)} research track(s) failed and were excluded from synthesis.")

    return ResearchQuality(
        source_count=len(unique_source_urls),
        unique_domain_count=len(domains),
        citation_count=citation_count,
        citation_coverage=round(citation_coverage, 2),
        success_rate=round(success_rate, 2),
        confidence_score=confidence_score,
        warnings=warnings,
    )


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator
