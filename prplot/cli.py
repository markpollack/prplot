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
from .cuts import CutRegistry


class PRCompleter(Completer):
    """Custom completer for PR analysis queries."""

    def __init__(self, data_loader: PRDataLoader, cut_registry: CutRegistry = None):
        self.data_loader = data_loader
        self.cut_registry = cut_registry
        self.field_info = data_loader.get_field_info()
        self.df = data_loader.get_data()

        # Command keywords
        self.commands = [
            'HIST', 'PLOT', 'TREND', 'BAR', 'STATS', 'IDENTIFY',
            'WHERE', 'BY', 'VS', 'AND', 'OR', 'NOT',
            'LIKE', 'IN', 'CONTAINS', 'save', 'export',
            'help', 'fields', 'quit', 'exit',
            'cut', 'uncut', 'cuts', 'source'
        ]

        # Field names (including nested fields)
        self.fields = list(self.field_info.keys())
        self.nested_fields = self._build_nested_fields()

        # Common operators
        self.operators = ['=', '!=', '<', '<=', '>', '>=', 'LIKE', 'IN', 'CONTAINS']

    def _build_nested_fields(self):
        """Build a dictionary of nested field completions."""
        nested_fields = {}

        for col in self.df.columns:
            # Sample the first non-null value to check if it's a dict
            sample = None
            for val in self.df[col].dropna():
                if isinstance(val, dict):
                    sample = val
                    break

            if sample:
                # Get keys from the dictionary
                nested_fields[col] = list(sample.keys())

        return nested_fields

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

        # Complete $cut references
        if last_word.startswith('$') and self.cut_registry:
            prefix = last_word[1:]  # strip the $
            for name in self.cut_registry.list_all():
                if name.startswith(prefix):
                    yield Completion(f"${name}", start_position=-len(last_word))
            return

        # Complete commands at the start
        if len(words) == 1:
            for cmd in self.commands:
                if cmd.lower().startswith(last_word.lower()):
                    yield Completion(cmd.lower(), start_position=-len(last_word))

        # Complete field names after commands or operators
        prev_word = words[-2].upper() if len(words) >= 2 else ""
        if prev_word in ['HIST', 'PLOT', 'TREND', 'BAR', 'STATS', 'IDENTIFY', 'BY', 'VS', 'WHERE'] or any(op in prev_word for op in self.operators):
            # Handle nested field completion (user. -> user.login, user.id, etc.)
            if '.' in last_word:
                field_part, sub_part = last_word.rsplit('.', 1)
                if field_part in self.nested_fields:
                    for subfield in self.nested_fields[field_part]:
                        nested_field = f"{field_part}.{subfield}"
                        if nested_field.lower().startswith(last_word.lower()):
                            yield Completion(nested_field, start_position=-len(last_word))
            else:
                # Regular field completion
                for field in self.fields:
                    if field.lower().startswith(last_word.lower()):
                        yield Completion(field, start_position=-len(last_word))

                # Also complete with nested field prefixes (user -> user.)
                for field in self.nested_fields:
                    if field.lower().startswith(last_word.lower()):
                        yield Completion(f"{field}.", start_position=-len(last_word))

        # Complete operators after field names (including nested fields)
        if len(words) >= 2:
            prev_field = words[-2]
            is_valid_field = (prev_field in self.fields or
                            ('.' in prev_field and prev_field.split('.')[0] in self.nested_fields))
            if is_valid_field:
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

    def __init__(self, json_file: str, plain: bool = False, init_file: str = None):
        """Initialize CLI with data file."""
        self.plain = plain
        self.init_file = init_file
        self.console = Console(no_color=True, highlight=False) if plain else Console()

        try:
            self.data_loader = PRDataLoader(json_file)
            self.parser = QueryParser()
            self.query_engine = QueryEngine(self.data_loader.get_data())
            self.visualizer = Visualizer()
            self.cut_registry = CutRegistry()

            if not plain:
                self.completer = PRCompleter(self.data_loader, self.cut_registry)
                history_file = os.path.expanduser("~/.prplot_history")
                self.history = FileHistory(history_file)

        except Exception as e:
            self.console.print(f"[red]Error loading data: {e}[/red]")
            sys.exit(1)

    def run(self):
        """Run the interactive CLI."""
        self._print_welcome()

        if self.init_file:
            self._handle_source(f"source {self.init_file}")

        while True:
            try:
                if self.plain:
                    query = input("prplot> ").strip()
                else:
                    query = prompt(
                        "prplot> ",
                        completer=self.completer,
                        history=self.history,
                        complete_while_typing=True
                    ).strip()

                if not query:
                    continue

                if query.lower() in ['quit', 'exit', 'q']:
                    break

                self._dispatch(query)

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use 'quit' or 'exit' to leave[/yellow]")
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")

        self.console.print("[green]Goodbye![/green]")

    def _dispatch(self, query: str):
        """Dispatch a single command."""
        if query.lower() == 'help':
            self._show_help()
        elif query.lower() == 'fields':
            self._show_fields()
        elif query.lower() == 'cuts':
            self._handle_cuts_list()
        elif query.lower().startswith('cut '):
            self._handle_cut_define(query)
        elif query.lower().startswith('uncut '):
            self._handle_cut_remove(query)
        elif query.lower().startswith('source '):
            self._handle_source(query)
        elif query.lower().startswith('save '):
            filename = query[5:].strip()
            self.visualizer.save_plot(filename)
        elif query.lower().startswith('export '):
            self._handle_export(query)
        else:
            # Resolve $cut references before dispatch
            if '$' in query:
                try:
                    query = self.cut_registry.resolve(query)
                except ValueError as e:
                    self.console.print(f"[red]Cut error: {e}[/red]")
                    return

            if query.lower().startswith('identify '):
                self._handle_identify(query)
            else:
                self._execute_query(query)

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
  WHERE label_names CONTAINS 'vector'
  WHERE author LIKE '%spring%'
  WHERE state IN ('open', 'closed')
  WHERE author NOT IN ('alice', 'bob')
  WHERE label_names NOT CONTAINS 'bug'
  WHERE created_at_dt > now-30d
  WHERE updated_at_dt < now-6M

[blue]Cut Commands (named reusable filters):[/blue]
  cut <name> <expression>              - Define a named cut
  uncut <name>                         - Remove a named cut
  cuts                                 - List all defined cuts

  Example:
    cut trusted author IN ('sdeleuze', 'markpollack')
    cut fresh created_at_dt > now-7d
    identify $trusted AND $fresh

[blue]Utility Commands:[/blue]
  source <file>                          - Execute commands from a file
  fields                                 - Show available fields
  identify WHERE condition               - Find specific PRs in a table
  save filename.png                      - Save current plot
  export WHERE condition TO file.json   - Export filtered data
  help                                   - Show this help
  quit/exit                              - Exit

[blue]Example Queries:[/blue]
  hist age_days
  plot comments vs age_days where state = 'open'
  trend created_at_dt by author
  bar label_names where time_bucket = '1-3 months'
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
        try:
            # Use the parser to handle both syntaxes:
            # 1. identify condition
            # 2. identify field where condition
            parsed_query = self.parser.parse_command(query)

            # Extract the WHERE clause from the parsed result
            where_clause = parsed_query['where']
            filtered_df = self.query_engine._apply_where_clause(
                self.data_loader.get_data(), where_clause
            )

            if len(filtered_df) == 0:
                self.console.print("[yellow]No PRs found matching criteria[/yellow]")
                return

            # Create table of matching PRs
            condition_text = query[9:].strip()  # Remove "identify " prefix
            table = Table(title=f"PRs matching: {condition_text}")
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
                    str(row['comment_count'])
                )

            self.console.print(table)

            # Print full URLs for easy copy-paste
            self.console.print("\n[dim]Full URLs:[/dim]")
            for _, row in display_df.iterrows():
                self.console.print(f"[dim]PR {row['number']}:[/dim] {row['html_url']}")

            if len(filtered_df) > 20:
                self.console.print(f"\n[yellow]Showing top 20 by age. Total matches: {len(filtered_df)}[/yellow]")

            self.console.print(f"\n[dim]💡 Tip: Copy URLs above to open in browser, or use Cmd/Ctrl+Click if your terminal supports it[/dim]")

        except Exception as e:
            self.console.print(f"[red]Identify error: {e}[/red]")

    def _handle_cut_define(self, query: str):
        """Handle cut definition: cut <name> <expression>."""
        parts = query.split(None, 2)
        if len(parts) < 3:
            self.console.print("[red]Usage: cut <name> <expression>[/red]")
            return
        name = parts[1]
        expression = parts[2]
        self.cut_registry.define(name, expression)
        self.console.print(f"Cut '${name}' defined: {expression}")

    def _handle_cut_remove(self, query: str):
        """Handle cut removal: uncut <name>."""
        parts = query.split()
        if len(parts) < 2:
            self.console.print("[red]Usage: uncut <name>[/red]")
            return
        name = parts[1]
        try:
            self.cut_registry.remove(name)
            self.console.print(f"Cut '${name}' removed")
        except KeyError:
            self.console.print(f"[red]Cut '${name}' not found[/red]")

    def _handle_source(self, query: str):
        """Handle source command: source <filename>."""
        filename = query.split(None, 1)[1].strip() if len(query.split(None, 1)) > 1 else ""
        if not filename:
            self.console.print("[red]Usage: source <filename>[/red]")
            return
        if not os.path.exists(filename):
            self.console.print(f"[red]File not found: {filename}[/red]")
            return
        count = 0
        with open(filename) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                try:
                    self._dispatch(line)
                    count += 1
                except Exception as e:
                    self.console.print(f"[red]Error in '{line}': {e}[/red]")
        self.console.print(f"Sourced {count} commands from {filename}")

    def _handle_cuts_list(self):
        """Handle cuts listing."""
        cuts = self.cut_registry.list_all()
        if not cuts:
            self.console.print("No cuts defined")
            return
        table = Table(title="Defined Cuts")
        table.add_column("Name", style="cyan")
        table.add_column("Expression", style="white")
        for name, expr in cuts.items():
            table.add_row(f"${name}", expr)
        self.console.print(table)


def main():
    """Main entry point."""
    args = sys.argv[1:]
    plain = "--plain" in args
    if plain:
        args.remove("--plain")

    init_file = None
    if "--init" in args:
        idx = args.index("--init")
        if idx + 1 >= len(args):
            print("Error: --init requires a filename")
            sys.exit(1)
        init_file = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

    if len(args) != 1:
        print("Usage: python -m prplot [--plain] [--init <file>] <json_file>")
        sys.exit(1)

    json_file = args[0]
    if not os.path.exists(json_file):
        print(f"Error: File {json_file} not found")
        sys.exit(1)

    cli = PRAnalysisCLI(json_file, plain=plain, init_file=init_file)
    cli.run()


if __name__ == "__main__":
    main()