# Recruiter Brief

## Project

Market Data Feed Quality Gate

## One-Line Signal

An operator-readable gate that turns market-data sequencing, timestamp sanity, stale-feed detection, crossed quote checks, and latency telemetry into a clear trust score and operator verdict.

## Why It Matters

Market data quality problems can corrupt research results, replay traces, dashboards, and risk systems. This project demonstrates the engineering discipline of checking the feed before trusting the analysis.

## Evidence To Review

- `src/market_data_feed_quality_gate/core.py`
- `tests/test_feed_quality_gate.py`
- `tests/test_cli_and_docs.py`
- `docs/paper.md`

## Boundaries

This project is public-safe, not financial advice, not a production trading system, and not connected to a broker or exchange.
