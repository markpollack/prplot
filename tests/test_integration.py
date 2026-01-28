"""Integration tests for prplot using pexpect."""

import os
import pytest
import pexpect

FIXTURE = os.path.join(os.path.dirname(__file__), "fixture_prs.json")


@pytest.fixture
def prplot():
    """Spawn prplot in --plain mode, wait for prompt, yield child, then quit."""
    child = pexpect.spawn(
        "python3", ["-m", "prplot", "--plain", FIXTURE],
        encoding="utf-8", timeout=10,
    )
    child.expect("prplot>")
    yield child
    child.sendline("quit")
    child.expect(pexpect.EOF)
    child.close()


def send_and_capture(child, command):
    """Send a command and return the output before the next prompt."""
    child.sendline(command)
    child.expect("prplot>")
    return child.before


def test_startup_loads_5_prs(prplot):
    assert "Loaded 5 PRs" in prplot.before


def test_fields_shows_new_schema(prplot):
    output = send_and_capture(prplot, "fields")
    assert "comment_count" in output
    assert "label_count" in output
    assert "label_names" in output
    assert "author" in output
    # Old schema fields should not appear
    assert "primary_label" not in output
    assert "total_reactions" not in output


def test_identify_all_open(prplot):
    output = send_and_capture(prplot, 'identify state = "open"')
    for pr in ["5356", "5355", "5354", "5351", "5349"]:
        assert pr in output


def test_identify_by_author(prplot):
    output = send_and_capture(prplot, 'identify author = "sdeleuze"')
    assert "5354" in output
    assert "5351" not in output


def test_identify_label_contains(prplot):
    output = send_and_capture(prplot, 'identify label_names CONTAINS "Bedrock"')
    assert "5351" in output


def test_date_shorthand_recent(prplot):
    output = send_and_capture(prplot, "identify created_at_dt > now-30d")
    for pr in ["5356", "5355", "5354", "5351", "5349"]:
        assert pr in output


def test_date_shorthand_old(prplot):
    output = send_and_capture(prplot, "identify created_at_dt < now-1y")
    assert "No PRs found" in output


def test_stats_count(prplot):
    output = send_and_capture(prplot, "stats comment_count")
    assert "Count" in output
    assert "5" in output
