from pathlib import Path

from market_data_feed_quality_gate.core import (
    FeedEvent,
    QualityThresholds,
    evaluate_feed,
    write_quality_report,
)


def test_clean_feed_passes_with_latency_and_trust_metrics() -> None:
    events = [
        FeedEvent(sequence=1, symbol="NVDA", exchange_ts_ns=1_000, receive_ts_ns=1_220, bid=900.10, ask=900.12, size=100),
        FeedEvent(sequence=2, symbol="NVDA", exchange_ts_ns=2_000, receive_ts_ns=2_260, bid=900.15, ask=900.18, size=120),
        FeedEvent(sequence=3, symbol="NVDA", exchange_ts_ns=3_000, receive_ts_ns=3_250, bid=900.20, ask=900.23, size=140),
    ]

    report = evaluate_feed(events, QualityThresholds(max_latency_ns=500, max_stale_gap_ns=1_500))

    assert report.symbol == "NVDA"
    assert report.verdict == "pass"
    assert report.trust_score == 100
    assert report.sequence_gap_count == 0
    assert report.p99_latency_ns == 260
    assert report.operator_summary == "Feed is trusted for downstream replay and research review."


def test_degraded_feed_detects_gaps_stale_ticks_and_crossed_quotes() -> None:
    events = [
        FeedEvent(sequence=10, symbol="MU", exchange_ts_ns=1_000, receive_ts_ns=1_250, bid=130.00, ask=130.05, size=100),
        FeedEvent(sequence=12, symbol="MU", exchange_ts_ns=6_000, receive_ts_ns=8_500, bid=130.10, ask=130.00, size=80),
        FeedEvent(sequence=11, symbol="MU", exchange_ts_ns=5_500, receive_ts_ns=9_000, bid=130.12, ask=130.16, size=90),
    ]

    report = evaluate_feed(events, QualityThresholds(max_latency_ns=1_000, max_stale_gap_ns=2_000))

    assert report.verdict == "reject"
    assert report.trust_score == 25
    assert report.sequence_gap_count == 1
    assert report.out_of_order_count == 1
    assert report.stale_gap_count == 1
    assert report.crossed_quote_count == 1
    assert "sequence gap" in report.failed_checks
    assert "out-of-order event" in report.failed_checks
    assert "stale feed gap" in report.failed_checks
    assert "crossed quote" in report.failed_checks
    assert report.operator_summary == "Feed is rejected until sequencing, latency, and quote integrity are reviewed."


def test_reports_are_written_as_markdown_and_json(tmp_path: Path) -> None:
    events = [
        FeedEvent(sequence=1, symbol="SPY", exchange_ts_ns=1_000, receive_ts_ns=1_400, bid=540.00, ask=540.02, size=100),
        FeedEvent(sequence=2, symbol="SPY", exchange_ts_ns=2_000, receive_ts_ns=2_450, bid=540.03, ask=540.06, size=100),
    ]
    report = evaluate_feed(events, QualityThresholds(max_latency_ns=700, max_stale_gap_ns=1_500))

    markdown_path, json_path = write_quality_report(report, tmp_path)

    markdown = markdown_path.read_text(encoding="utf-8")
    json_text = json_path.read_text(encoding="utf-8")
    assert "Market Data Feed Quality Gate Report" in markdown
    assert "SPY" in markdown
    assert "Trust score: 100" in markdown
    assert '"verdict": "pass"' in json_text
    assert '"p99_latency_ns": 450' in json_text
