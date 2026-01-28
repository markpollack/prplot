"""Integration tests for prplot using pexpect."""

import os
import tempfile
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


def test_cut_define_and_use(prplot):
    send_and_capture(prplot, 'cut open state = "open"')
    output = send_and_capture(prplot, "identify $open")
    for pr in ["5356", "5355", "5354", "5351", "5349"]:
        assert pr in output


def test_cut_compose(prplot):
    send_and_capture(prplot, 'cut open state = "open"')
    send_and_capture(prplot, 'cut byauthor author = "sdeleuze"')
    output = send_and_capture(prplot, "identify $open AND $byauthor")
    assert "5354" in output
    assert "5351" not in output


def test_cuts_list(prplot):
    send_and_capture(prplot, 'cut mycut age_days > 10')
    output = send_and_capture(prplot, "cuts")
    assert "$mycut" in output
    assert "age_days > 10" in output


def test_uncut(prplot):
    send_and_capture(prplot, 'cut tmp age_days > 10')
    send_and_capture(prplot, "uncut tmp")
    output = send_and_capture(prplot, "cuts")
    assert "No cuts defined" in output


def test_undefined_cut_error(prplot):
    output = send_and_capture(prplot, "identify $nope")
    assert "Undefined cut" in output


def test_source_loads_cuts(prplot):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".prplot", delete=False) as f:
        f.write('cut open state = "open"\n')
        f.write("cut commented comment_count > 0\n")
        f.name
    try:
        output = send_and_capture(prplot, f"source {f.name}")
        assert "Sourced 2 commands" in output
        output = send_and_capture(prplot, "cuts")
        assert "$open" in output
        assert "$commented" in output
    finally:
        os.unlink(f.name)


def test_source_comments_skipped(prplot):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".prplot", delete=False) as f:
        f.write("# this is a comment\n")
        f.write("\n")
        f.write('cut mycut state = "open"\n')
        f.write("# another comment\n")
        f.name
    try:
        output = send_and_capture(prplot, f"source {f.name}")
        assert "Sourced 1 commands" in output
        output = send_and_capture(prplot, "cuts")
        assert "$mycut" in output
    finally:
        os.unlink(f.name)


def test_source_file_not_found(prplot):
    output = send_and_capture(prplot, "source /nonexistent/file.prplot")
    assert "File not found" in output


def test_source_nested(prplot):
    """source files can source other files."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".prplot", delete=False) as inner:
        inner.write('cut inner_cut age_days > 10\n')
        inner.flush()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".prplot", delete=False) as outer:
            outer.write(f"source {inner.name}\n")
            outer.write('cut outer_cut comment_count > 0\n')
            outer.flush()
            try:
                output = send_and_capture(prplot, f"source {outer.name}")
                assert "Sourced 2 commands" in output
                output = send_and_capture(prplot, "cuts")
                assert "$inner_cut" in output
                assert "$outer_cut" in output
            finally:
                os.unlink(inner.name)
                os.unlink(outer.name)


def test_init_flag_loads_cuts():
    """--init flag auto-sources a file on startup."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".prplot", delete=False) as f:
        f.write('cut startup_cut age_days > 5\n')
        f.flush()
        try:
            child = pexpect.spawn(
                "python3", ["-m", "prplot", "--plain", "--init", f.name, FIXTURE],
                encoding="utf-8", timeout=10,
            )
            child.expect("prplot>")
            # The init file should have been sourced during startup
            child.sendline("cuts")
            child.expect("prplot>")
            output = child.before
            assert "$startup_cut" in output
            child.sendline("quit")
            child.expect(pexpect.EOF)
            child.close()
        finally:
            os.unlink(f.name)


def test_not_in_identify(prplot):
    """NOT with IN operator works in identify."""
    output = send_and_capture(
        prplot, 'identify NOT (author IN ("sdeleuze", "sobychacko"))'
    )
    assert "5354" not in output  # sdeleuze's PR excluded
    assert "5356" in output      # other author included


def test_cut_with_not(prplot):
    """Cut using NOT expression resolves and executes."""
    send_and_capture(
        prplot, 'cut others NOT (author IN ("sdeleuze", "sobychacko"))'
    )
    output = send_and_capture(prplot, "identify $others")
    assert "5354" not in output
    assert "5356" in output


def test_not_in_operator(prplot):
    """field NOT IN (...) syntax works."""
    output = send_and_capture(
        prplot, 'identify author NOT IN ("sdeleuze", "sobychacko")'
    )
    assert "5354" not in output  # sdeleuze's PR excluded
    assert "5356" in output


def test_not_contains_operator(prplot):
    """field NOT CONTAINS works."""
    output = send_and_capture(
        prplot, 'identify label_names NOT CONTAINS "Bedrock"'
    )
    assert "5351" not in output  # has Bedrock label
    assert "5356" in output
