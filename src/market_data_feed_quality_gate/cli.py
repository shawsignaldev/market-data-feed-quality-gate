from __future__ import annotations

import argparse
from pathlib import Path

from .core import FeedEvent, QualityThresholds, evaluate_feed, write_quality_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a public-safe market data feed quality gate.")
    parser.add_argument("--symbol", default="SPY", help="Synthetic symbol used in the sample feed.")
    parser.add_argument("--output-dir", default="reports", help="Directory for Markdown and JSON reports.")
    args = parser.parse_args(argv)

    events = sample_events(args.symbol)
    report = evaluate_feed(events, QualityThresholds(max_latency_ns=900, max_stale_gap_ns=1_500))
    markdown_path, json_path = write_quality_report(report, Path(args.output_dir))
    print(f"Wrote {markdown_path}")
    print(f"Wrote {json_path}")
    print(f"Verdict: {report.verdict} | Trust score: {report.trust_score}")
    return 0


def sample_events(symbol: str) -> list[FeedEvent]:
    return [
        FeedEvent(sequence=1, symbol=symbol, exchange_ts_ns=1_000, receive_ts_ns=1_320, bid=100.10, ask=100.12, size=100),
        FeedEvent(sequence=2, symbol=symbol, exchange_ts_ns=2_000, receive_ts_ns=2_330, bid=100.11, ask=100.14, size=120),
        FeedEvent(sequence=3, symbol=symbol, exchange_ts_ns=3_000, receive_ts_ns=3_360, bid=100.15, ask=100.18, size=90),
        FeedEvent(sequence=4, symbol=symbol, exchange_ts_ns=4_000, receive_ts_ns=4_390, bid=100.17, ask=100.20, size=130),
    ]
