"""
Query execution engine for filtering and aggregating PR data.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import re
from datetime import datetime


class QueryEngine:
    """Executes parsed queries against PR DataFrame."""

    def __init__(self, df: pd.DataFrame):
        """Initialize with PR DataFrame."""
        self.df = df

    def execute_query(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a parsed query and return results."""
        # Apply WHERE clause filtering
        filtered_df = self.df
        if parsed_query.get('where'):
            filtered_df = self._apply_where_clause(filtered_df, parsed_query['where'])

        # Execute the specific command type
        query_type = parsed_query['type']

        if query_type == 'hist':
            return self._execute_hist(filtered_df, parsed_query)
        elif query_type == 'plot':
            return self._execute_plot(filtered_df, parsed_query)
        elif query_type == 'trend':
            return self._execute_trend(filtered_df, parsed_query)
        elif query_type == 'bar':
            return self._execute_bar(filtered_df, parsed_query)
        elif query_type == 'stats':
            return self._execute_stats(filtered_df, parsed_query)
        else:
            raise ValueError(f"Unknown query type: {query_type}")

    def _apply_where_clause(self, df: pd.DataFrame, where_clause: Dict[str, Any]) -> pd.DataFrame:
        """Apply WHERE clause filtering to DataFrame."""
        return df[self._evaluate_condition(df, where_clause)]

    def _evaluate_condition(self, df: pd.DataFrame, condition: Dict[str, Any]) -> pd.Series:
        """Evaluate a condition and return boolean Series."""
        cond_type = condition['type']

        if cond_type == 'comparison':
            return self._evaluate_comparison(df, condition)
        elif cond_type == 'boolean':
            left_result = self._evaluate_condition(df, condition['left'])
            right_result = self._evaluate_condition(df, condition['right'])

            if condition['operator'] == 'AND':
                return left_result & right_result
            elif condition['operator'] == 'OR':
                return left_result | right_result
            else:
                raise ValueError(f"Unknown boolean operator: {condition['operator']}")
        else:
            raise ValueError(f"Unknown condition type: {cond_type}")

    def _evaluate_comparison(self, df: pd.DataFrame, condition: Dict[str, Any]) -> pd.Series:
        """Evaluate a comparison condition."""
        field = condition['field']
        operator = condition['operator']
        value = condition['value']

        # Handle nested field access (e.g., labels_assigned.label)
        series = self._get_field_series(df, field)

        # Handle boolean conversion for string boolean values
        if series.dtype == 'bool' and isinstance(value, str):
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False

        if operator in ['=', '==']:
            return series == value
        elif operator in ['!=', '<>']:
            return series != value
        elif operator == '<':
            return series < value
        elif operator == '<=':
            return series <= value
        elif operator == '>':
            return series > value
        elif operator == '>=':
            return series >= value
        elif operator == 'LIKE':
            # SQL LIKE with % wildcards
            pattern = value.replace('%', '.*').replace('_', '.')
            return series.astype(str).str.match(pattern, case=False, na=False)
        elif operator == 'CONTAINS':
            # Check if field contains value (for arrays/lists)
            if hasattr(series.iloc[0], '__iter__') and not isinstance(series.iloc[0], str):
                return series.apply(lambda x: value in x if x is not None else False)
            else:
                return series.astype(str).str.contains(str(value), case=False, na=False)
        elif operator == 'IN':
            return series.isin(value if isinstance(value, list) else [value])
        else:
            raise ValueError(f"Unknown comparison operator: {operator}")

    def _get_field_series(self, df: pd.DataFrame, field: str) -> pd.Series:
        """Get Series for field, handling nested access."""
        if '.' in field:
            # Handle nested field access
            parts = field.split('.')
            if parts[0] in df.columns:
                series = df[parts[0]]
                for part in parts[1:]:
                    if part == 'label' and parts[0] == 'labels_assigned':
                        # Special handling for labels_assigned.label
                        return series.apply(
                            lambda x: x[0]['label'] if isinstance(x, list) and len(x) > 0 else None
                        )
                    else:
                        # Generic nested access
                        series = series.apply(
                            lambda x: x.get(part) if isinstance(x, dict) else None
                        )
                return series
            else:
                raise ValueError(f"Field not found: {parts[0]}")
        else:
            if field in df.columns:
                return df[field]
            else:
                raise ValueError(f"Field not found: {field}")

    def _execute_hist(self, df: pd.DataFrame, query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute histogram query."""
        field = query['field']
        series = self._get_field_series(df, field)

        # Remove null values
        series = series.dropna()

        return {
            'type': 'histogram',
            'field': field,
            'data': series.tolist(),
            'count': len(series),
            'stats': {
                'mean': float(series.mean()) if series.dtype in ['int64', 'float64'] else None,
                'median': float(series.median()) if series.dtype in ['int64', 'float64'] else None,
                'std': float(series.std()) if series.dtype in ['int64', 'float64'] else None,
                'min': series.min(),
                'max': series.max(),
                'unique': series.nunique()
            }
        }

    def _execute_plot(self, df: pd.DataFrame, query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute scatter/line plot query."""
        x_field = query['field']
        y_field = query.get('y_field')

        if y_field is None:
            # Single variable plot (line plot over index)
            x_series = self._get_field_series(df, x_field)
            return {
                'type': 'line',
                'x_field': 'index',
                'y_field': x_field,
                'x_data': list(range(len(x_series))),
                'y_data': x_series.tolist(),
                'count': len(x_series)
            }
        else:
            # Scatter plot
            x_series = self._get_field_series(df, x_field)
            y_series = self._get_field_series(df, y_field)

            # Remove rows where either value is null
            valid_mask = x_series.notna() & y_series.notna()
            filtered_df = df[valid_mask]
            x_clean = x_series[valid_mask]
            y_clean = y_series[valid_mask]

            # Include PR numbers for identification
            pr_numbers = filtered_df['number'].tolist() if 'number' in filtered_df.columns else []

            return {
                'type': 'scatter',
                'x_field': x_field,
                'y_field': y_field,
                'x_data': x_clean.tolist(),
                'y_data': y_clean.tolist(),
                'pr_numbers': pr_numbers,
                'count': len(x_clean)
            }

    def _execute_trend(self, df: pd.DataFrame, query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trend/time series query."""
        time_field = query['field']
        group_by = query.get('group_by')

        time_series = self._get_field_series(df, time_field)

        if group_by:
            # Group by another field
            group_series = self._get_field_series(df, group_by)
            grouped_data = {}

            for group_val in group_series.dropna().unique():
                mask = group_series == group_val
                group_times = time_series[mask].dropna()

                if len(group_times) > 0:
                    # Count by time period (daily, weekly, monthly based on data range)
                    if hasattr(group_times.iloc[0], 'date'):
                        # DateTime field - group by month
                        monthly_counts = group_times.dt.to_period('M').value_counts().sort_index()
                        grouped_data[str(group_val)] = {
                            'times': [str(period) for period in monthly_counts.index],
                            'counts': monthly_counts.tolist()
                        }
                    else:
                        # Non-datetime field - just count occurrences
                        value_counts = group_times.value_counts().sort_index()
                        grouped_data[str(group_val)] = {
                            'values': value_counts.index.tolist(),
                            'counts': value_counts.tolist()
                        }

            return {
                'type': 'trend_grouped',
                'time_field': time_field,
                'group_by': group_by,
                'data': grouped_data,
                'total_count': len(df)
            }
        else:
            # Simple time trend
            clean_times = time_series.dropna()

            if hasattr(clean_times.iloc[0], 'date'):
                # DateTime field
                monthly_counts = clean_times.dt.to_period('M').value_counts().sort_index()
                return {
                    'type': 'trend',
                    'time_field': time_field,
                    'times': [str(period) for period in monthly_counts.index],
                    'counts': monthly_counts.tolist(),
                    'total_count': len(clean_times)
                }
            else:
                # Non-datetime field
                value_counts = clean_times.value_counts().sort_index()
                return {
                    'type': 'trend',
                    'time_field': time_field,
                    'values': value_counts.index.tolist(),
                    'counts': value_counts.tolist(),
                    'total_count': len(clean_times)
                }

    def _execute_bar(self, df: pd.DataFrame, query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute bar chart query."""
        field = query['field']
        group_by = query.get('group_by')

        series = self._get_field_series(df, field)

        if group_by:
            # Grouped bar chart
            group_series = self._get_field_series(df, group_by)
            cross_tab = pd.crosstab(series, group_series, dropna=False)

            return {
                'type': 'bar_grouped',
                'field': field,
                'group_by': group_by,
                'categories': cross_tab.index.tolist(),
                'groups': cross_tab.columns.tolist(),
                'data': cross_tab.values.tolist(),
                'total_count': len(df)
            }
        else:
            # Simple bar chart
            value_counts = series.value_counts()

            return {
                'type': 'bar',
                'field': field,
                'categories': value_counts.index.tolist(),
                'counts': value_counts.tolist(),
                'total_count': len(df)
            }

    def _execute_stats(self, df: pd.DataFrame, query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute statistical summary query."""
        field = query['field']
        group_by = query.get('group_by')

        series = self._get_field_series(df, field)

        if group_by:
            # Grouped statistics
            group_series = self._get_field_series(df, group_by)
            grouped_stats = {}

            for group_val in group_series.dropna().unique():
                mask = group_series == group_val
                group_data = series[mask].dropna()

                if len(group_data) > 0:
                    if group_data.dtype in ['int64', 'float64']:
                        grouped_stats[str(group_val)] = {
                            'count': len(group_data),
                            'mean': float(group_data.mean()),
                            'median': float(group_data.median()),
                            'std': float(group_data.std()),
                            'min': float(group_data.min()),
                            'max': float(group_data.max())
                        }
                    else:
                        grouped_stats[str(group_val)] = {
                            'count': len(group_data),
                            'unique': group_data.nunique(),
                            'top': str(group_data.mode().iloc[0]) if len(group_data.mode()) > 0 else None
                        }

            return {
                'type': 'stats_grouped',
                'field': field,
                'group_by': group_by,
                'data': grouped_stats,
                'total_count': len(df)
            }
        else:
            # Simple statistics
            clean_data = series.dropna()

            if clean_data.dtype in ['int64', 'float64']:
                return {
                    'type': 'stats',
                    'field': field,
                    'count': len(clean_data),
                    'mean': float(clean_data.mean()),
                    'median': float(clean_data.median()),
                    'std': float(clean_data.std()),
                    'min': float(clean_data.min()),
                    'max': float(clean_data.max()),
                    'total_count': len(df)
                }
            else:
                return {
                    'type': 'stats',
                    'field': field,
                    'count': len(clean_data),
                    'unique': clean_data.nunique(),
                    'top': str(clean_data.mode().iloc[0]) if len(clean_data.mode()) > 0 else None,
                    'value_counts': clean_data.value_counts().head(10).to_dict(),
                    'total_count': len(df)
                }