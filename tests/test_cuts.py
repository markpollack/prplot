"""Unit tests for CutRegistry."""

import pytest
from prplot.cuts import CutRegistry


def test_define_and_resolve():
    r = CutRegistry()
    r.define("c", "x > 1")
    assert r.resolve("$c") == "(x > 1)"


def test_resolve_multiple():
    r = CutRegistry()
    r.define("a", "x > 1")
    r.define("b", "y < 10")
    assert r.resolve("$a AND $b") == "(x > 1) AND (y < 10)"


def test_resolve_undefined_raises():
    r = CutRegistry()
    with pytest.raises(ValueError, match="Undefined cut: \\$nope"):
        r.resolve("$nope")


def test_remove():
    r = CutRegistry()
    r.define("c", "x > 1")
    r.remove("c")
    with pytest.raises(ValueError):
        r.resolve("$c")


def test_remove_missing_raises():
    r = CutRegistry()
    with pytest.raises(KeyError):
        r.remove("nope")


def test_overwrite():
    r = CutRegistry()
    r.define("c", "x > 1")
    r.define("c", "x > 99")
    assert r.resolve("$c") == "(x > 99)"


def test_list_all():
    r = CutRegistry()
    r.define("a", "x > 1")
    r.define("b", "y < 10")
    assert r.list_all() == {"a": "x > 1", "b": "y < 10"}


def test_list_empty():
    r = CutRegistry()
    assert r.list_all() == {}


def test_no_recursive():
    r = CutRegistry()
    r.define("a", "$b > 1")
    r.define("b", "y < 10")
    # Single pass — $b inside a's expression is NOT resolved
    assert r.resolve("$a") == "($b > 1)"


def test_no_dollar_passthrough():
    r = CutRegistry()
    assert r.resolve("x > 1") == "x > 1"


def test_resolve_in_context():
    r = CutRegistry()
    r.define("open", "state = 'open'")
    result = r.resolve('identify $open')
    assert result == "identify (state = 'open')"
