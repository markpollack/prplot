"""
PR Analysis CLI Tool - SQL-Style Interactive Explorer

A Python-based interactive CLI tool for rapid PR data exploration and visualization,
with ROOT/PAW-inspired single-line queries using familiar SQL WHERE clause syntax.
"""

__version__ = "0.1.0"
__author__ = "Mark Pollack"

from .cli import main
from .data_loader import PRDataLoader
from .query_engine import QueryEngine
from .visualizer import Visualizer

__all__ = ["main", "PRDataLoader", "QueryEngine", "Visualizer"]