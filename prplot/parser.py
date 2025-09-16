"""
Query parser for SQL-style WHERE clauses and plotting commands.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from pyparsing import (
    Word, alphas, alphanums, nums, Literal, QuotedString,
    CaselessKeyword, infixNotation, opAssoc, pyparsing_common,
    ZeroOrMore, OneOrMore, Optional as PPOptional, Group, Combine
)


class QueryParser:
    """Parses plotting commands with SQL-style WHERE clauses."""

    def __init__(self):
        self._setup_grammar()

    def _setup_grammar(self):
        """Set up pyparsing grammar for query language."""

        # Basic tokens
        identifier = Word(alphas + "_", alphanums + "_" + ".")
        integer = pyparsing_common.signed_integer()
        real = pyparsing_common.real()
        string_literal = QuotedString('"', escChar='\\') | QuotedString("'", escChar='\\')

        # Field references (support dot notation like labels_assigned.label)
        field = identifier

        # Values
        value = real | integer | string_literal | identifier

        # Comparison operators
        eq_op = Literal("=") | Literal("==")
        ne_op = Literal("!=") | Literal("<>")
        lt_op = Literal("<")
        le_op = Literal("<=")
        gt_op = Literal(">")
        ge_op = Literal(">=")
        like_op = CaselessKeyword("LIKE")
        in_op = CaselessKeyword("IN")
        contains_op = CaselessKeyword("CONTAINS")

        comparison_op = (eq_op | ne_op | le_op | ge_op | lt_op | gt_op |
                        like_op | in_op | contains_op)

        # List for IN operator
        value_list = Literal("(") + Group(value + ZeroOrMore(Literal(",") + value)) + Literal(")")

        # Comparison expressions
        comparison = Group(field + comparison_op + (value_list | value))

        # Boolean expressions with AND/OR
        bool_expr = infixNotation(
            comparison,
            [
                (CaselessKeyword("NOT"), 1, opAssoc.RIGHT),
                (CaselessKeyword("AND"), 2, opAssoc.LEFT),
                (CaselessKeyword("OR"), 2, opAssoc.LEFT),
            ]
        )

        # WHERE clause
        where_clause = CaselessKeyword("WHERE") + bool_expr

        # Plot commands
        hist_cmd = CaselessKeyword("HIST") + field + PPOptional(where_clause)
        plot_cmd = (CaselessKeyword("PLOT") + field +
                   PPOptional(CaselessKeyword("VS") + field) +
                   PPOptional(where_clause))
        trend_cmd = (CaselessKeyword("TREND") + field +
                    PPOptional(CaselessKeyword("BY") + field) +
                    PPOptional(where_clause))
        bar_cmd = (CaselessKeyword("BAR") + field +
                  PPOptional(CaselessKeyword("BY") + field) +
                  PPOptional(where_clause))
        stats_cmd = (CaselessKeyword("STATS") + field +
                    PPOptional(CaselessKeyword("BY") + field) +
                    PPOptional(where_clause))
        identify_cmd = (CaselessKeyword("IDENTIFY") + bool_expr) | (CaselessKeyword("IDENTIFY") + field + where_clause)

        # Complete command
        self.command = hist_cmd | plot_cmd | trend_cmd | bar_cmd | stats_cmd | identify_cmd

        # Store sub-parsers for reuse
        self.where_parser = where_clause
        self.comparison_parser = comparison

    def parse_command(self, command_str: str) -> Dict[str, Any]:
        """Parse a complete plotting command."""
        try:
            result = self.command.parseString(command_str, parseAll=True)
            return self._interpret_parse_result(result)
        except Exception as e:
            raise ValueError(f"Parse error: {str(e)}")

    def parse_where_clause(self, where_str: str) -> Dict[str, Any]:
        """Parse just a WHERE clause."""
        try:
            result = self.where_parser.parseString(where_str, parseAll=True)
            return self._interpret_where_result(result[1])  # Skip "WHERE" keyword
        except Exception as e:
            raise ValueError(f"WHERE clause parse error: {str(e)}")

    def _interpret_parse_result(self, result) -> Dict[str, Any]:
        """Interpret the parsed command result."""
        tokens = list(result)

        command_type = tokens[0].lower()

        if command_type == 'identify':
            # IDENTIFY supports two forms:
            # 1. IDENTIFY <condition>
            # 2. IDENTIFY <field> WHERE <condition>
            if len(tokens) >= 3 and isinstance(tokens[2], str) and tokens[2].upper() == 'WHERE':
                # Form 2: IDENTIFY field WHERE condition
                return {
                    'type': 'identify',
                    'field': tokens[1],
                    'where': self._interpret_where_result(tokens[3])
                }
            else:
                # Form 1: IDENTIFY condition (original)
                return {
                    'type': 'identify',
                    'where': self._interpret_where_result(tokens[1])
                }

        # Other commands: COMMAND field [options]
        command = {
            'type': command_type,
            'field': tokens[1],
            'where': None
        }

        i = 2
        while i < len(tokens):
            token = tokens[i]

            if isinstance(token, str):
                if token.upper() == "VS":
                    command['y_field'] = tokens[i + 1]
                    i += 2
                elif token.upper() == "BY":
                    command['group_by'] = tokens[i + 1]
                    i += 2
                elif token.upper() == "WHERE":
                    command['where'] = self._interpret_where_result(tokens[i + 1])
                    i += 2
                else:
                    i += 1
            else:
                # This might be a WHERE clause result
                if command['where'] is None:
                    command['where'] = self._interpret_where_result(token)
                i += 1

        return command

    def _interpret_where_result(self, where_result) -> Dict[str, Any]:
        """Interpret a WHERE clause parse result into filter conditions."""
        if isinstance(where_result, str):
            return {'type': 'literal', 'value': where_result}

        # Handle pyparsing Group objects
        if hasattr(where_result, 'asList'):
            where_result = where_result.asList()

        if isinstance(where_result, list):
            # Handle simple comparison: [field, operator, value]
            if len(where_result) == 3 and isinstance(where_result[0], str) and isinstance(where_result[1], str):
                field, op, value = where_result
                return {
                    'type': 'comparison',
                    'field': field,
                    'operator': op.upper(),
                    'value': value
                }

            # Handle boolean operations with infixNotation structure
            # infixNotation creates nested lists like [[field, op, value], 'AND', [field, op, value]]
            if len(where_result) >= 3:
                # Check if it's a boolean expression pattern
                for i in range(1, len(where_result), 2):
                    if where_result[i] in ['AND', 'OR']:
                        # This is a boolean expression
                        left = self._interpret_where_result(where_result[i-1])
                        right = self._interpret_where_result(where_result[i+1])
                        return {
                            'type': 'boolean',
                            'operator': where_result[i],
                            'left': left,
                            'right': right
                        }

            # Handle single element list (wrapped comparison)
            if len(where_result) == 1:
                return self._interpret_where_result(where_result[0])

        return {'type': 'unknown', 'value': str(where_result)}


def test_parser():
    """Test the query parser with sample commands."""
    parser = QueryParser()

    test_commands = [
        "HIST age_days",
        "HIST age_days WHERE state = 'open'",
        "PLOT comments VS age_days",
        "PLOT comments VS age_days WHERE state = 'open' AND comments > 5",
        "TREND created_at_dt BY primary_label",
        "BAR primary_label",
        "STATS age_days BY state WHERE time_bucket = '1-3 months'"
    ]

    for cmd in test_commands:
        try:
            result = parser.parse_command(cmd)
            print(f"'{cmd}' -> {result}")
        except Exception as e:
            print(f"'{cmd}' -> ERROR: {e}")


if __name__ == "__main__":
    test_parser()