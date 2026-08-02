# Market Data Feed Quality Gate

`market-data-feed-quality-gate` is a public-safe market data feed quality gate for checking whether a stream is trustworthy enough for replay, research review, or downstream operator dashboards.

The project combines sequence-gap detection, timestamp sanity, stale-feed detection, crossed quote checks, latency summaries, trust scoring, and an operator verdict in one deterministic report. It is designed as a portfolio-grade bridge between market infrastructure, FPGA-style packet discipline, and cyber-physical operator reliability.

## What It Proves

- Feed quality should be measured before strategy research consumes a market-data stream.
- Sequence integrity, timestamp sanity, stale-feed detection, and crossed quote checks can be tested with deterministic public fixtures.
- Operator-facing systems need a clear pass, watchlist, or reject verdict instead of raw counters alone.
- The same logic can support Python golden models, FPGA/SmartNIC packet paths, replay engines, and control-room dashboards.

## Quick Start

```powershell
python -m pytest -q
python -m market_data_feed_quality_gate --symbol NVDA --output-dir reports
```

The CLI writes:

- `reports/market_data_feed_quality_gate_report.md`
- `reports/market_data_feed_quality_gate_report.json`

## Architecture

```text
Synthetic feed events
        |
        v
Sequence and ordering checks
        |
        v
Timestamp sanity and stale-feed detection
        |
        v
Quote integrity and latency summary
        |
        v
Trust score plus operator verdict
        |
        v
Markdown and JSON evidence reports
```

## Public-Safe Boundary

This repository uses synthetic events only. It is public-safe, not financial advice, not a production trading system, and not connected to a broker or exchange.
