"""
Interactive CLI for PR data analysis with SQL-style queries.
"""

import sys
import os
import pandas as pd
from typing import Dict, List, Optional
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter, Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import confirm
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from .data_loader import PRDataLoader
from .parser import QueryParser
from .query_engine import QueryEngine
from .visualizer import Visualizer


class PRCompleter(Completer):
    """Custom completer for PR analysis queries."""

    def __init__(self, data_loader: PRDataLoader):
        self.data_loader = data_loader
        self.field_info = data_loader.get_field_info()

        # Command keywords
        self.commands = [
            'HIST', 'PLOT', 'TREND', 'BAR', 'STATS', 'IDENTIFY',
            'WHERE', 'BY', 'VS', 'AND', 'OR', 'NOT',
            'LIKE', 'IN', 'CONTAINS', 'save', 'export',
            'help', 'fields', 'quit', 'exit'
        ]

        # Field names
        self.fields = list(self.field_info.keys())

        # Common operators
        self.operators = ['=', '!=', '<', '<=', '>', '>=', 'LIKE', 'IN', 'CONTAINS']

    def get_completions(self, document, complete_event):
        """Generate completions based on current context."""
        text = document.text_before_cursor
        words = text.split()

        if not words:
            # Start with commands
            for cmd in self.commands:
                yield Completion(cmd.lower(), start_position=0)
            return

        last_word = words[-1] if words else ""

        # Complete commands at the start
        if len(words) == 1:
            for cmd in self.commands:
                if cmd.lower().startswith(last_word.lower()):
                    yield Completion(cmd.lower(), start_position=-len(last_word))

        # Complete field names after commands or operators
        prev_word = words[-2].upper() if len(words) >= 2 else ""
        if prev_word in ['HIST', 'PLOT', 'TREND', 'BAR', 'STATS', 'IDENTIFY', 'BY', 'VS', 'WHERE'] or any(op in prev_word for op in self.operators):
            for field in self.fields:
                if field.lower().startswith(last_word.lower()):
                    yield Completion(field, start_position=-len(last_word))

        # Complete operators after field names
        if len(words) >= 2 and words[-2] in self.fields:
            for op in self.operators:
                if op.lower().startswith(last_word.lower()):
                    yield Completion(op, start_position=-len(last_word))

        # Complete values based on field type
        if len(words) >= 3 and words[-3] in self.fields:
            field_name = words[-3]
            field_info = self.field_info.get(field_name, {})
            sample_values = field_info.get('sample_values', [])

            for value in sample_values:
                value_str = f"'{value}'" if isinstance(value, str) else str(value)
                if value_str.lower().startswith(last_word.lower()):
                    yield Completion(value_str, start_position=-len(last_word))


class PRAnalysisCLI:
    """Interactive CLI for PR data analysis."""

    def __init__(self, json_file: str):
        """Initialize CLI with data file."""
        self.console = Console()

        try:
            self.data_loader = PRDataLoader(json_file)
            self.parser = QueryParser()
            self.query_engine = QueryEngine(self.data_loader.get_data())
            self.visualizer = Visualizer()

            self.completer = PRCompleter(self.data_loader)

            # Set up history file
            history_file = os.path.expanduser("~/.prplot_history")
            self.history = FileHistory(history_file)

        except Exception as e:
            self.console.print(f"[red]Error loading data: {e}[/red]")
            sys.exit(1)

    def run(self):
        """Run the interactive CLI."""
        self._print_welcome()

        while True:
            try:
                # Get user input with completion and history
                query = prompt(
                    "prplot> ",
                    completer=self.completer,
                    history=self.history,
                    complete_while_typing=True
                ).strip()

                if not query:
                    continue

                # Handle special commands
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                elif query.lower() == 'help':
                    self._show_help()
                elif query.lower() == 'fields':
                    self._show_fields()
                elif query.lower().startswith('save '):
                    filename = query[5:].strip()
                    self.visualizer.save_plot(filename)
                elif query.lower().startswith('export '):
                    self._handle_export(query)
                elif query.lower().startswith('identify '):
                    self._handle_identify(query)
                else:
                    # Parse and execute query
                    self._execute_query(query)

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use 'quit' or 'exit' to leave[/yellow]")
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")

        self.console.print("[green]Goodbye![/green]")

    def _print_welcome(self):
        """Print welcome message."""
        self.console.print("\n[bold blue]PR Analysis CLI[/bold blue]")
        self.console.print("SQL-style queries for GitHub PR data exploration")
        self.console.print(f"Loaded {len(self.data_loader.get_data())} PRs")
        self.console.print("\nType 'help' for commands, 'fields' for available fields, 'quit' to exit\n")

    def _show_help(self):
        """Show help information."""
        help_text = """
[bold]Available Commands:[/bold]

[blue]Plot Commands:[/blue]
  HIST field [WHERE condition]           - Histogram of field values
  PLOT field [VS field2] [WHERE ...]     - Scatter plot or line plot
  TREND field [BY groupfield] [WHERE ..] - Time series trend
  BAR field [BY groupfield] [WHERE ...]  - Bar chart
  STATS field [BY groupfield] [WHERE ..] - Statistical summary

[blue]WHERE Clause Examples:[/blue]
  WHERE state = 'open'
  WHERE age_days > 90 AND comments > 5
  WHERE primary_label CONTAINS 'vector'
  WHERE author LIKE '%spring%'
  WHERE state IN ('open', 'closed')

[blue]Utility Commands:[/blue]
  fields                                 - Show available fields
  identify WHERE condition               - Find specific PRs in a table
  save filename.png                      - Save current plot
  export WHERE condition TO file.json   - Export filtered data
  help                                   - Show this help
  quit/exit                              - Exit

[blue]Example Queries:[/blue]
  hist age_days
  plot comments vs age_days where state = 'open'
  trend created_at_dt by primary_label
  bar primary_label where time_bucket = '1-3 months'
  stats comments by state
"""
        self.console.print(help_text)

    def _show_fields(self):
        """Show available fields with types."""
        table = Table(title="Available Fields")
        table.add_column("Field", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Unique Values", style="green")
        table.add_column("Sample Values", style="white")

        field_info = self.data_loader.get_field_info()

        for field, info in sorted(field_info.items()):
            sample_str = ", ".join(str(v) for v in info.get('sample_values', [])[:3])
            if len(info.get('sample_values', [])) > 3:
                sample_str += "..."

            table.add_row(
                field,
                info['type'],
                str(info['unique_values']),
                sample_str
            )

        self.console.print(table)

    def _execute_query(self, query: str):
        """Parse and execute a query."""
        try:
            # Parse the query
            parsed_query = self.parser.parse_command(query)

            # Execute the query
            result = self.query_engine.execute_query(parsed_query)

            # Visualize the result
            self.visualizer.visualize(result)

        except Exception as e:
            self.console.print(f"[red]Query error: {e}[/red]")

    def _handle_export(self, query: str):
        """Handle export command."""
        # Simple export parsing: "export WHERE condition TO filename"
        parts = query.lower().split(' to ')
        if len(parts) != 2:
            self.console.print("[red]Export syntax: export WHERE condition TO filename.json[/red]")
            return

        where_part = parts[0].replace('export ', '').strip()
        filename = parts[1].strip()

        try:
            # Parse WHERE clause
            if where_part.startswith('where '):
                where_clause = self.parser.parse_where_clause(where_part)
                filtered_df = self.query_engine._apply_where_clause(
                    self.data_loader.get_data(), where_clause
                )
            else:
                filtered_df = self.data_loader.get_data()

            # Convert to JSON and save
            export_data = {
                'prs': filtered_df.to_dict('records'),
                'count': len(filtered_df),
                'exported_at': str(pd.Timestamp.now())
            }

            import json
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

            self.console.print(f"[green]Exported {len(filtered_df)} PRs to {filename}[/green]")

        except Exception as e:
            self.console.print(f"[red]Export error: {e}[/red]")

    def _handle_identify(self, query: str):
        """Handle identify command to find specific PRs."""
        # Parse: "identify WHERE condition" or "identify comments > 10 and age_days > 100"
        if query.lower().startswith('identify where '):
            where_part = query[15:].strip()
        elif query.lower().startswith('identify '):
            where_part = "WHERE " + query[9:].strip()
        else:
            self.console.print("[red]Identify syntax: identify WHERE condition[/red]")
            return

        try:
            # Parse WHERE clause
            where_clause = self.parser.parse_where_clause(where_part)
            filtered_df = self.query_engine._apply_where_clause(
                self.data_loader.get_data(), where_clause
            )

            if len(filtered_df) == 0:
                self.console.print("[yellow]No PRs found matching criteria[/yellow]")
                return

            # Create table of matching PRs
            table = Table(title=f"PRs matching: {where_part}")
            table.add_column("PR#", style="cyan")
            table.add_column("Title", style="white", max_width=50)
            table.add_column("State", style="green")
            table.add_column("Age (days)", style="yellow")
            table.add_column("Comments", style="magenta")

            # Sort by age (most interesting first)
            display_df = filtered_df.nlargest(20, 'age_days') if len(filtered_df) > 20 else filtered_df

            for _, row in display_df.iterrows():
                table.add_row(
                    str(row['number']),
                    str(row['title'])[:47] + "..." if len(str(row['title'])) > 50 else str(row['title']),
                    str(row['state']),
                    str(row['age_days']),
                    str(row['comments'])
                )

            self.console.print(table)

            if len(filtered_df) > 20:
                self.console.print(f"[yellow]Showing top 20 by age. Total matches: {len(filtered_df)}[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Identify error: {e}[/red]")


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python -m prplot <json_file>")
        sys.exit(1)

    json_file = sys.argv[1]
    if not os.path.exists(json_file):
        print(f"Error: File {json_file} not found")
        sys.exit(1)

    cli = PRAnalysisCLI(json_file)
    cli.run()


if __name__ == "__main__":
    main()