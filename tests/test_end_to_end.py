"""End-to-end test: jbang collect → prplot analyze."""

import os
import json
import subprocess
import shutil
import pytest
import pexpect

JBANG = shutil.which("jbang")

pytestmark = pytest.mark.skipif(
    JBANG is None, reason="jbang not installed"
)


@pytest.fixture(scope="module")
def collected_json(tmp_path_factory):
    """Collect 3 PRs via jbang and return the output file path."""
    outdir = tmp_path_factory.mktemp("collect")
    outfile = outdir / "prs.json"
    result = subprocess.run(
        [
            JBANG, "collect@github-collector",
            "--type", "prs",
            "--pr-state", "open",
            "--max-issues", "3",
            "--single-file",
            "-o", str(outfile),
        ],
        capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, f"jbang collect failed:\n{result.stderr}"
    assert outfile.exists(), "Output file not created"
    return str(outfile)


def test_jbang_collect_produces_valid_json(collected_json):
    with open(collected_json) as f:
        data = json.load(f)
    assert "prs" in data
    assert len(data["prs"]) == 3
    # Verify ISO date strings (not arrays)
    pr = data["prs"][0]
    assert isinstance(pr["created_at"], str)
    assert "T" in pr["created_at"]


def test_jbang_collect_help():
    result = subprocess.run(
        [JBANG, "collect@github-collector", "--help"],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0
    assert "OPTIONS" in result.stdout
    assert "--repo" in result.stdout
    assert "--type" in result.stdout


def test_prplot_loads_collected_data(collected_json):
    child = pexpect.spawn(
        "python3", ["-m", "prplot", "--plain", collected_json],
        encoding="utf-8", timeout=10,
    )
    child.expect("prplot>")
    assert "Loaded 3 PRs" in child.before

    # Run a query
    child.sendline('identify state = "open"')
    child.expect("prplot>")
    output = child.before
    # Should find PRs (all are open)
    assert "PR#" in output or "number" in output.lower()

    child.sendline("fields")
    child.expect("prplot>")
    output = child.before
    assert "comment_count" in output
    assert "author" in output

    child.sendline("quit")
    child.expect(pexpect.EOF)
    child.close()
