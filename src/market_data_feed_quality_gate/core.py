from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class FeedEvent:
    sequence: int
    symbol: str
    exchange_ts_ns: int
    receive_ts_ns: int
    bid: float
    ask: float
    size: int


@dataclass(frozen=True)
class QualityThresholds:
    max_latency_ns: int = 1_000
    max_stale_gap_ns: int = 2_000


@dataclass(frozen=True)
class FeedQualityReport:
    symbol: str
    event_count: int
    verdict: str
    trust_score: int
    p99_latency_ns: int
    max_latency_ns: int
    sequence_gap_count: int
    out_of_order_count: int
    stale_gap_count: int
    crossed_quote_count: int
    failed_checks: list[str]
    operator_summary: str


def evaluate_feed(events: list[FeedEvent], thresholds: QualityThresholds | None = None) -> FeedQualityReport:
    if not events:
        raise ValueError("at least one feed event is required")

    thresholds = thresholds or QualityThresholds()
    symbol = events[0].symbol
    sequence_gap_count = 0
    out_of_order_count = 0
    stale_gap_count = 0
    crossed_quote_count = 0
    latencies: list[int] = []

    previous_sequence = events[0].sequence
    previous_exchange_ts = events[0].exchange_ts_ns

    for index, event in enumerate(events):
        if event.symbol != symbol:
            raise ValueError("all feed events in a report must share one symbol")
        if event.ask <= event.bid:
            crossed_quote_count += 1
        latencies.append(max(0, event.receive_ts_ns - event.exchange_ts_ns))
        if index == 0:
            continue

        if event.sequence <= previous_sequence:
            out_of_order_count += 1
        elif event.sequence > previous_sequence + 1:
            sequence_gap_count += event.sequence - previous_sequence - 1

        if event.exchange_ts_ns - previous_exchange_ts > thresholds.max_stale_gap_ns:
            stale_gap_count += 1

        previous_sequence = event.sequence
        previous_exchange_ts = event.exchange_ts_ns

    p99_latency_ns = _percentile_high(latencies, 0.99)
    max_latency_ns = max(latencies)
    failed_checks = _failed_checks(
        sequence_gap_count,
        out_of_order_count,
        stale_gap_count,
        crossed_quote_count,
        p99_latency_ns,
        thresholds,
    )
    trust_score = _trust_score(sequence_gap_count, out_of_order_count, stale_gap_count, crossed_quote_count)
    verdict = "pass" if not failed_checks else "watchlist" if trust_score >= 70 else "reject"
    operator_summary = _operator_summary(verdict)

    return FeedQualityReport(
        symbol=symbol,
        event_count=len(events),
        verdict=verdict,
        trust_score=trust_score,
        p99_latency_ns=p99_latency_ns,
        max_latency_ns=max_latency_ns,
        sequence_gap_count=sequence_gap_count,
        out_of_order_count=out_of_order_count,
        stale_gap_count=stale_gap_count,
        crossed_quote_count=crossed_quote_count,
        failed_checks=failed_checks,
        operator_summary=operator_summary,
    )


def write_quality_report(report: FeedQualityReport, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = output_dir / "market_data_feed_quality_gate_report.md"
    json_path = output_dir / "market_data_feed_quality_gate_report.json"

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True), encoding="utf-8")
    return markdown_path, json_path


def _percentile_high(values: list[int], percentile: float) -> int:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = max(0, min(len(ordered) - 1, int(round(percentile * (len(ordered) - 1)))))
    return ordered[rank]


def _failed_checks(
    sequence_gap_count: int,
    out_of_order_count: int,
    stale_gap_count: int,
    crossed_quote_count: int,
    p99_latency_ns: int,
    thresholds: QualityThresholds,
) -> list[str]:
    checks: list[str] = []
    if sequence_gap_count:
        checks.append("sequence gap")
    if out_of_order_count:
        checks.append("out-of-order event")
    if stale_gap_count:
        checks.append("stale feed gap")
    if crossed_quote_count:
        checks.append("crossed quote")
    if p99_latency_ns > thresholds.max_latency_ns:
        checks.append("timestamp sanity latency breach")
    return checks


def _trust_score(
    sequence_gap_count: int,
    out_of_order_count: int,
    stale_gap_count: int,
    crossed_quote_count: int,
) -> int:
    penalty = (
        min(sequence_gap_count, 3) * 20
        + min(out_of_order_count, 3) * 20
        + min(stale_gap_count, 3) * 20
        + min(crossed_quote_count, 3) * 15
    )
    return max(0, 100 - penalty)


def _operator_summary(verdict: str) -> str:
    if verdict == "pass":
        return "Feed is trusted for downstream replay and research review."
    if verdict == "watchlist":
        return "Feed can be replayed with caution while failed checks are investigated."
    return "Feed is rejected until sequencing, latency, and quote integrity are reviewed."


def _render_markdown(report: FeedQualityReport) -> str:
    checks = ", ".join(report.failed_checks) if report.failed_checks else "none"
    return "\n".join(
        [
            "# Market Data Feed Quality Gate Report",
            "",
            f"Symbol: {report.symbol}",
            f"Verdict: {report.verdict}",
            f"Trust score: {report.trust_score}",
            f"Event count: {report.event_count}",
            "",
            "## Timing",
            "",
            f"P99 latency ns: {report.p99_latency_ns}",
            f"Max latency ns: {report.max_latency_ns}",
            "",
            "## Integrity Checks",
            "",
            f"Sequence gaps: {report.sequence_gap_count}",
            f"Out-of-order events: {report.out_of_order_count}",
            f"Stale feed gaps: {report.stale_gap_count}",
            f"Crossed quotes: {report.crossed_quote_count}",
            f"Failed checks: {checks}",
            "",
            "## Operator Verdict",
            "",
            report.operator_summary,
            "",
            "This report is public-safe, not financial advice, not a production trading system, and not connected to a broker or exchange.",
            "",
        ]
    )
