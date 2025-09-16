#!/usr/bin/env python3
"""
Test script for prplot functionality with sample queries.
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prplot.data_loader import PRDataLoader
from prplot.parser import QueryParser
from prplot.query_engine import QueryEngine
from prplot.visualizer import Visualizer


def test_basic_functionality():
    """Test basic functionality with sample queries."""

    # Check if data file exists
    json_file = "all_prs_labeled.json"
    if not os.path.exists(json_file):
        print(f"Error: {json_file} not found in current directory")
        return False

    try:
        # Load data
        print("Loading data...")
        loader = PRDataLoader(json_file)
        df = loader.get_data()
        print(f"Loaded {len(df)} PRs")

        # Initialize components
        parser = QueryParser()
        engine = QueryEngine(df)
        viz = Visualizer()

        # Test queries
        test_queries = [
            "HIST age_days",
            "HIST state",
            "PLOT comments VS age_days WHERE state = 'open'",
            "BAR primary_label",
            "STATS age_days BY state",
            "TREND created_at_dt BY primary_label WHERE age_days < 365"
        ]

        print("\nTesting queries:")
        print("=" * 50)

        for query in test_queries:
            print(f"\nQuery: {query}")
            try:
                # Parse query
                parsed = parser.parse_command(query)
                print(f"  Parsed: {parsed['type']} on {parsed['field']}")

                # Execute query
                result = engine.execute_query(parsed)
                print(f"  Result: {result['type']} with {result.get('count', 'N/A')} data points")

                # Note: We don't actually show plots in this test, just verify they work
                print("  ✓ Query executed successfully")

            except Exception as e:
                print(f"  ✗ Error: {e}")
                return False

        print("\n" + "=" * 50)
        print("All tests passed! 🎉")
        print("\nTo run the interactive CLI:")
        print(f"  python -m prplot {json_file}")
        print("  # or")
        print(f"  prplot {json_file}")

        return True

    except Exception as e:
        print(f"Test failed: {e}")
        return False


def show_sample_session():
    """Show what a sample interactive session would look like."""

    sample_session = '''
Sample Interactive Session:
==========================

$ prplot all_prs_labeled.json

PR Analysis CLI
SQL-style queries for GitHub PR data exploration
Loaded 199 PRs

Type 'help' for commands, 'fields' for available fields, 'quit' to exit

prplot> fields
[Shows table of all available fields with types and sample values]

prplot> hist age_days
[Histogram showing distribution of PR ages]

prplot> hist age_days where state = 'open'
[Histogram of only open PRs]

prplot> plot comments vs age_days where state = 'open'
[Scatter plot with trend line showing comment activity vs age]

prplot> bar primary_label where age_days > 90
[Bar chart of label distribution for older PRs]

prplot> trend created_at_dt by primary_label
[Multi-line time series showing PR creation trends by label]

prplot> stats comments by state
Statistics for comments grouped by state:
========================================

state = closed:
  Count:  150
  Mean:   2.34
  Median: 1.00
  ...

prplot> export where primary_label = 'MCP' to mcp_prs.json
Exported 15 PRs to mcp_prs.json

prplot> save pr_trends.png
Plot saved to pr_trends.png

prplot> quit
Goodbye!
'''

    print(sample_session)


if __name__ == "__main__":
    print("PRPlot Test Suite")
    print("================")

    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        show_sample_session()
    else:
        success = test_basic_functionality()

        if success:
            print("\nRun with --demo to see sample session output")
        else:
            sys.exit(1)