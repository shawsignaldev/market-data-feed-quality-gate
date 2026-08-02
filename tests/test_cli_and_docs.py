import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_cli_writes_sample_report(tmp_path: Path) -> None:
    env = {"PYTHONPATH": str(ROOT / "src")}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "market_data_feed_quality_gate",
            "--symbol",
            "ORCL",
            "--output-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
        env=env,
    )

    assert "market_data_feed_quality_gate_report.md" in result.stdout
    assert (tmp_path / "market_data_feed_quality_gate_report.md").exists()
    assert (tmp_path / "market_data_feed_quality_gate_report.json").exists()


def test_docs_state_public_safe_boundaries() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    paper = (ROOT / "docs" / "paper.md").read_text(encoding="utf-8")
    brief = (ROOT / "docs" / "recruiter-brief.md").read_text(encoding="utf-8")
    combined = "\n".join([readme, paper, brief])

    required = [
        "market data feed quality gate",
        "sequence-gap detection",
        "timestamp sanity",
        "stale-feed detection",
        "crossed quote",
        "operator verdict",
        "public-safe",
        "not financial advice",
        "not a production trading system",
        "not connected to a broker or exchange",
    ]
    for term in required:
        assert term in combined
