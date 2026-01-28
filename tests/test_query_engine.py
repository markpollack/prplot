"""Unit tests for QueryEngine, focusing on NOT evaluation."""

import pandas as pd
import pytest
from prplot.query_engine import QueryEngine


@pytest.fixture
def engine():
    df = pd.DataFrame({
        'author': ['alice', 'bob', 'carol', 'alice', 'dave'],
        'age_days': [10, 200, 50, 300, 5],
        'comment_count': [3, 0, 7, 1, 0],
        'state': ['open', 'open', 'closed', 'open', 'open'],
    })
    return QueryEngine(df)


def test_not_comparison(engine):
    cond = {'type': 'not', 'operand': {
        'type': 'comparison', 'field': 'state', 'operator': '=', 'value': 'open'
    }}
    result = engine._apply_where_clause(engine.df, cond)
    assert list(result['state']) == ['closed']


def test_not_in(engine):
    cond = {'type': 'not', 'operand': {
        'type': 'comparison', 'field': 'author', 'operator': 'IN',
        'value': ['alice', 'bob']
    }}
    result = engine._apply_where_clause(engine.df, cond)
    assert sorted(result['author'].tolist()) == ['carol', 'dave']


def test_not_and(engine):
    """NOT combined with AND: NOT (author IN (...)) AND age_days > 100."""
    cond = {
        'type': 'boolean', 'operator': 'AND',
        'left': {'type': 'not', 'operand': {
            'type': 'comparison', 'field': 'author', 'operator': 'IN',
            'value': ['alice', 'bob']
        }},
        'right': {
            'type': 'comparison', 'field': 'age_days', 'operator': '>', 'value': 100
        }
    }
    result = engine._apply_where_clause(engine.df, cond)
    # carol has age 50 (excluded), dave has age 5 (excluded) -> empty
    assert len(result) == 0


def test_not_or(engine):
    """NOT combined with OR."""
    cond = {
        'type': 'boolean', 'operator': 'OR',
        'left': {'type': 'not', 'operand': {
            'type': 'comparison', 'field': 'author', 'operator': '=', 'value': 'alice'
        }},
        'right': {
            'type': 'comparison', 'field': 'age_days', 'operator': '>', 'value': 200
        }
    }
    result = engine._apply_where_clause(engine.df, cond)
    # NOT alice -> bob, carol, dave; age>200 -> alice(300) only
    # alice(10) is neither NOT-alice nor age>200, so excluded
    assert len(result) == 4


def test_double_not(engine):
    cond = {'type': 'not', 'operand': {
        'type': 'not', 'operand': {
            'type': 'comparison', 'field': 'state', 'operator': '=', 'value': 'open'
        }
    }}
    result = engine._apply_where_clause(engine.df, cond)
    assert all(r == 'open' for r in result['state'])
    assert len(result) == 4


def test_basic_in(engine):
    cond = {
        'type': 'comparison', 'field': 'author', 'operator': 'IN',
        'value': ['alice', 'carol']
    }
    result = engine._apply_where_clause(engine.df, cond)
    assert sorted(result['author'].tolist()) == ['alice', 'alice', 'carol']


def test_not_in_via_not_wrapper(engine):
    """NOT IN produces same result as NOT wrapping IN."""
    cond_not_in = {'type': 'not', 'operand': {
        'type': 'comparison', 'field': 'author', 'operator': 'IN',
        'value': ['alice', 'bob']
    }}
    result = engine._apply_where_clause(engine.df, cond_not_in)
    assert sorted(result['author'].tolist()) == ['carol', 'dave']


def test_comparison_operators(engine):
    for op, field, val, expected_count in [
        ('=', 'state', 'open', 4),
        ('!=', 'state', 'open', 1),
        ('<>', 'state', 'open', 1),
        ('>', 'age_days', 100, 2),
        ('>=', 'age_days', 200, 2),
        ('<', 'age_days', 10, 1),
        ('<=', 'age_days', 10, 2),
    ]:
        cond = {'type': 'comparison', 'field': field, 'operator': op, 'value': val}
        result = engine._apply_where_clause(engine.df, cond)
        assert len(result) == expected_count, f"Failed for {field} {op} {val}"
