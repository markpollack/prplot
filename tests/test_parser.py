"""Unit tests for QueryParser, focusing on NOT and boolean logic."""

import pytest
from prplot.parser import QueryParser


@pytest.fixture
def parser():
    return QueryParser()


# --- NOT support ---

def test_not_simple_comparison(parser):
    result = parser.parse_command("identify NOT age_days > 90")
    where = result['where']
    assert where['type'] == 'not'
    assert where['operand']['type'] == 'comparison'
    assert where['operand']['field'] == 'age_days'


def test_not_in_expression(parser):
    result = parser.parse_command("identify NOT (author IN ('tzolov', 'markpollack'))")
    where = result['where']
    assert where['type'] == 'not'
    assert where['operand']['type'] == 'comparison'
    assert where['operand']['operator'] == 'IN'
    assert where['operand']['value'] == ['tzolov', 'markpollack']


def test_not_combined_with_and(parser):
    result = parser.parse_command(
        "identify NOT (author IN ('tzolov', 'markpollack')) AND age_days > 180"
    )
    where = result['where']
    assert where['type'] == 'boolean'
    assert where['operator'] == 'AND'
    assert where['left']['type'] == 'not'
    assert where['right']['type'] == 'comparison'
    assert where['right']['field'] == 'age_days'


def test_not_combined_with_or(parser):
    result = parser.parse_command(
        "identify NOT age_days > 90 OR comment_count > 10"
    )
    where = result['where']
    assert where['type'] == 'boolean'
    assert where['operator'] == 'OR'
    assert where['left']['type'] == 'not'


def test_double_not(parser):
    result = parser.parse_command("identify NOT NOT age_days > 90")
    where = result['where']
    assert where['type'] == 'not'
    assert where['operand']['type'] == 'not'
    assert where['operand']['operand']['type'] == 'comparison'


# --- IN operator ---

def test_in_operator(parser):
    result = parser.parse_command("identify author IN ('alice', 'bob', 'carol')")
    where = result['where']
    assert where['type'] == 'comparison'
    assert where['operator'] == 'IN'
    assert where['value'] == ['alice', 'bob', 'carol']


def test_in_single_value(parser):
    result = parser.parse_command("identify author IN ('alice')")
    where = result['where']
    assert where['operator'] == 'IN'
    assert where['value'] == ['alice']


# --- Basic comparisons ---

def test_equality(parser):
    result = parser.parse_command("identify state = 'open'")
    where = result['where']
    assert where == {'type': 'comparison', 'field': 'state', 'operator': '=', 'value': 'open'}


def test_not_equal(parser):
    result = parser.parse_command("identify state != 'open'")
    where = result['where']
    assert where['operator'] == '!='


def test_not_equal_diamond(parser):
    result = parser.parse_command("identify state <> 'open'")
    where = result['where']
    assert where['operator'] == '<>'


def test_greater_than(parser):
    result = parser.parse_command("identify age_days > 90")
    where = result['where']
    assert where['operator'] == '>'
    assert where['value'] == 90


def test_less_equal(parser):
    result = parser.parse_command("identify age_days <= 30")
    where = result['where']
    assert where['operator'] == '<='


# --- Boolean logic ---

def test_and(parser):
    result = parser.parse_command("identify age_days > 90 AND comment_count > 5")
    where = result['where']
    assert where['type'] == 'boolean'
    assert where['operator'] == 'AND'


def test_or(parser):
    result = parser.parse_command("identify age_days > 90 OR comment_count > 5")
    where = result['where']
    assert where['type'] == 'boolean'
    assert where['operator'] == 'OR'


# --- Date literals ---

def test_date_relative_days(parser):
    result = parser.parse_command("identify created_at_dt > now-30d")
    where = result['where']
    assert where['value'] == 'now-30d'


def test_date_relative_months(parser):
    result = parser.parse_command("identify updated_at_dt < now-6M")
    where = result['where']
    assert where['value'] == 'now-6M'


def test_date_relative_years(parser):
    result = parser.parse_command("identify created_at_dt > now-1y")
    where = result['where']
    assert where['value'] == 'now-1y'


# --- LIKE / CONTAINS ---

def test_like(parser):
    result = parser.parse_command("identify author LIKE '%spring%'")
    where = result['where']
    assert where['operator'] == 'LIKE'


def test_contains(parser):
    result = parser.parse_command("identify label_names CONTAINS 'bug'")
    where = result['where']
    assert where['operator'] == 'CONTAINS'


# --- Plot commands with WHERE ---

def test_hist_where(parser):
    result = parser.parse_command("hist age_days where state = 'open'")
    assert result['type'] == 'hist'
    assert result['field'] == 'age_days'
    assert result['where']['type'] == 'comparison'


def test_plot_vs_where(parser):
    result = parser.parse_command("plot age_days vs comment_count where age_days > 90")
    assert result['type'] == 'plot'
    assert result['field'] == 'age_days'
    assert result['y_field'] == 'comment_count'
    assert result['where'] is not None


def test_bar_no_where(parser):
    result = parser.parse_command("bar author")
    assert result['type'] == 'bar'
    assert result['where'] is None


def test_hist_where_not(parser):
    result = parser.parse_command(
        "hist age_days where NOT (author IN ('tzolov', 'markpollack'))"
    )
    assert result['type'] == 'hist'
    assert result['where']['type'] == 'not'
    assert result['where']['operand']['operator'] == 'IN'


# --- NOT IN / NOT LIKE / NOT CONTAINS ---

def test_not_in(parser):
    result = parser.parse_command("identify author NOT IN ('alice', 'bob')")
    where = result['where']
    assert where['type'] == 'not'
    assert where['operand']['type'] == 'comparison'
    assert where['operand']['operator'] == 'IN'
    assert where['operand']['value'] == ['alice', 'bob']


def test_not_in_single_value(parser):
    result = parser.parse_command("identify author NOT IN ('alice')")
    where = result['where']
    assert where['type'] == 'not'
    assert where['operand']['operator'] == 'IN'
    assert where['operand']['value'] == ['alice']


def test_not_in_combined_with_and(parser):
    result = parser.parse_command(
        "identify author NOT IN ('alice', 'bob') AND age_days > 90"
    )
    where = result['where']
    assert where['type'] == 'boolean'
    assert where['operator'] == 'AND'
    assert where['left']['type'] == 'not'
    assert where['left']['operand']['operator'] == 'IN'
    assert where['right']['type'] == 'comparison'


def test_not_like(parser):
    result = parser.parse_command("identify author NOT LIKE '%spring%'")
    where = result['where']
    assert where['type'] == 'not'
    assert where['operand']['operator'] == 'LIKE'
    assert where['operand']['value'] == '%spring%'


def test_not_contains(parser):
    result = parser.parse_command("identify label_names NOT CONTAINS 'bug'")
    where = result['where']
    assert where['type'] == 'not'
    assert where['operand']['operator'] == 'CONTAINS'
    assert where['operand']['value'] == 'bug'


def test_not_in_equivalence(parser):
    """NOT IN and NOT (... IN ...) produce the same AST structure."""
    r1 = parser.parse_command("identify author NOT IN ('a', 'b')")
    r2 = parser.parse_command("identify NOT (author IN ('a', 'b'))")
    assert r1['where']['type'] == r2['where']['type'] == 'not'
    assert r1['where']['operand']['operator'] == r2['where']['operand']['operator'] == 'IN'
    assert r1['where']['operand']['value'] == r2['where']['operand']['value']


def test_hist_where_not_in(parser):
    result = parser.parse_command(
        "hist age_days where author NOT IN ('alice', 'bob')"
    )
    assert result['type'] == 'hist'
    assert result['where']['type'] == 'not'
    assert result['where']['operand']['operator'] == 'IN'
