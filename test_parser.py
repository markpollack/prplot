#!/usr/bin/env python3
"""
Comprehensive test cases for the query parser based on README examples.
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prplot.parser import QueryParser
import traceback


def test_parser_with_examples():
    """Test parser with all examples from README.md"""

    parser = QueryParser()

    # Test cases organized by command type
    test_cases = {
        "HIST Examples": [
            "hist age_days",
            "hist comments",
            "hist age_days where comments > 5",
            "hist comments where age_days > 90 and comments > 0",
        ],

        "PLOT Examples": [
            "plot age_days vs comments",
            "plot age_days vs activity_score",
            "plot age_days vs comments where comments > 5",
            "plot age_days vs total_reactions where age_days > 60 and comments > 2",
        ],

        "BAR Examples": [
            "bar primary_label",
            "bar time_bucket",
            "bar primary_label where comments > 3",
            "bar complexity where age_days > 90",
        ],

        "TREND Examples": [
            "trend created_at_dt",
            "trend created_at_dt by primary_label",
            "trend created_week where age_days < 120",
            "trend created_month by complexity where age_days > 30",
        ],

        "STATS Examples": [
            "stats comments",
            "stats age_days by complexity",
            "stats activity_score by primary_label",
            "stats comments by time_bucket where age_days > 60",
        ],

        "IDENTIFY Examples": [
            "identify comments > 10",
            "identify age_days > 200 and comments > 3",
            "identify age_days < 60 and activity_score > 15",
            "identify primary_label contains 'vector' and comments > 2",
            "identify age_days where age_days > 90 and comments > 5",  # New WHERE syntax
        ],

        "Complex WHERE Clauses": [
            "hist age_days where state = 'open'",
            "plot comments vs age_days where state = 'open' and comments > 5",
            "bar primary_label where created_year = 2024 and comments > 2",
            "stats age_days by author where comments > 0",
            "trend created_week by state where age_days < 90",
            "identify primary_label like '%vector%'",
            "identify author like '%spring%'",
            "identify state in ('open', 'closed')",
        ],

        "Edge Cases": [
            "HIST AGE_DAYS",  # uppercase
            "hist age_days WHERE comments > 5",  # mixed case
            "plot comments vs age_days where age_days>90",  # no spaces
            "bar primary_label where comments > 5 and age_days > 90 and activity_score > 10",  # multiple AND
            "identify comments > 5 or activity_score > 20",  # OR operator
            "stats comments where not comments = 0",  # NOT operator
            "identify primary_label contains 'MCP' or primary_label contains 'vector'",  # OR with CONTAINS
        ],

        "String and Number Values": [
            "identify state = 'open'",
            'identify author = "spring-user"',
            "identify comments = 5",
            "identify age_days >= 90.5",
            "identify primary_label != 'unknown'",
            "identify time_bucket <> 'invalid'",
        ],

        "Boolean Values": [
            "identify soft_approval_detected = true",
            "identify soft_approval_detected = false",
            "identify soft_approval_detected = True",
            "identify soft_approval_detected = FALSE",
            "identify is_draft = false",
        ],

        "Field References": [
            "identify labels_assigned.label contains 'test'",  # dot notation
            "plot labels_assigned.confidence vs comments",
            "stats labels_assigned.label by state",
        ]
    }

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    print("🧪 Testing Parser with README Examples")
    print("=" * 60)

    for category, queries in test_cases.items():
        print(f"\n📋 {category}")
        print("-" * 40)

        for query in queries:
            total_tests += 1
            try:
                result = parser.parse_command(query)
                print(f"✅ {query}")

                if result['type'] == 'identify':
                    print(f"   → identify with condition")
                else:
                    print(f"   → {result['type']} on {result['field']}")

                if 'y_field' in result:
                    print(f"   → y_field: {result['y_field']}")
                if 'group_by' in result:
                    print(f"   → group_by: {result['group_by']}")
                if result.get('where'):
                    print(f"   → where: {result['where']['type']}")
                passed_tests += 1

            except Exception as e:
                print(f"❌ {query}")
                print(f"   → ERROR: {e}")
                failed_tests.append((query, str(e)))

    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Summary")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {len(failed_tests)} ❌")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")

    if failed_tests:
        print(f"\n🔍 Failed Tests:")
        for query, error in failed_tests:
            print(f"  • {query}")
            print(f"    {error}")

    return len(failed_tests) == 0


def test_where_clause_parsing():
    """Test WHERE clause parsing specifically"""

    parser = QueryParser()

    where_tests = [
        "WHERE state = 'open'",
        "WHERE comments > 5",
        "WHERE age_days > 90 AND comments > 5",
        "WHERE state = 'open' OR state = 'closed'",
        "WHERE NOT comments = 0",
        "WHERE primary_label CONTAINS 'vector'",
        "WHERE author LIKE '%spring%'",
        "WHERE state IN ('open', 'closed')",
        "WHERE age_days > 90 AND comments > 5 AND activity_score > 10",
    ]

    print("\n🔍 Testing WHERE Clause Parsing")
    print("=" * 40)

    for where_clause in where_tests:
        try:
            result = parser.parse_where_clause(where_clause)
            print(f"✅ {where_clause}")
            print(f"   → {result}")
        except Exception as e:
            print(f"❌ {where_clause}")
            print(f"   → ERROR: {e}")


def test_command_edge_cases():
    """Test edge cases and potential breaking inputs"""

    parser = QueryParser()

    edge_cases = [
        # Empty/minimal
        "hist",  # Should fail - no field
        "plot x",  # Should work - single field plot
        "plot x vs",  # Should fail - incomplete

        # Weird spacing
        "hist  age_days",
        "plot comments    vs     age_days",
        "identify   comments>5",

        # Case variations
        "HIST age_days WHERE state='open'",
        "Plot Comments Vs Age_Days",
        "identify COMMENTS > 5 AND age_days < 100",

        # Special characters in strings
        "identify title contains 'fix: bug in feature'",
        "identify author = 'user@domain.com'",

        # Numeric edge cases
        "identify comments >= 0",
        "identify age_days < 365.25",
        "identify activity_score != -1",
    ]

    print("\n🎯 Testing Edge Cases")
    print("=" * 30)

    for query in edge_cases:
        try:
            result = parser.parse_command(query)
            print(f"✅ {query}")
        except Exception as e:
            print(f"❌ {query}")
            print(f"   → {e}")


if __name__ == "__main__":
    print("Parser Test Suite")
    print("================")

    # Run all tests
    success = test_parser_with_examples()
    test_where_clause_parsing()
    test_command_edge_cases()

    if success:
        print("\n🎉 All README examples passed!")
        sys.exit(0)
    else:
        print("\n🚨 Some tests failed - parser needs fixes")
        sys.exit(1)