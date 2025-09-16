"""
Visualization engine for generating plots from query results.
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import seaborn as sns
from datetime import datetime
import warnings

# Set up matplotlib for better defaults
plt.style.use('default')
sns.set_palette("husl")
warnings.filterwarnings('ignore', category=FutureWarning)


class Visualizer:
    """Creates visualizations from query results."""

    def __init__(self):
        """Initialize visualizer with default settings."""
        self.fig_size = (12, 8)
        self.dpi = 100
        self.current_fig = None

    def visualize(self, query_result: Dict[str, Any], title: Optional[str] = None) -> None:
        """Create visualization based on query result type."""
        result_type = query_result['type']

        if result_type == 'histogram':
            self._plot_histogram(query_result, title)
        elif result_type == 'scatter':
            self._plot_scatter(query_result, title)
        elif result_type == 'line':
            self._plot_line(query_result, title)
        elif result_type == 'trend':
            self._plot_trend(query_result, title)
        elif result_type == 'trend_grouped':
            self._plot_trend_grouped(query_result, title)
        elif result_type == 'bar':
            self._plot_bar(query_result, title)
        elif result_type == 'bar_grouped':
            self._plot_bar_grouped(query_result, title)
        elif result_type == 'stats':
            self._print_stats(query_result)
        elif result_type == 'stats_grouped':
            self._print_stats_grouped(query_result)
        else:
            print(f"Unknown result type: {result_type}")

        # Show the plot if one was created
        if self.current_fig is not None:
            plt.tight_layout()
            plt.show()

    def _plot_histogram(self, result: Dict[str, Any], title: Optional[str]) -> None:
        """Create histogram plot."""
        data = result['data']
        field = result['field']

        self.current_fig, ax = plt.subplots(figsize=self.fig_size, dpi=self.dpi)

        # Determine if data is numeric
        try:
            numeric_data = [float(x) for x in data if x is not None]
            is_numeric = True
        except (ValueError, TypeError):
            is_numeric = False

        if is_numeric and len(numeric_data) > 0:
            # Numeric histogram
            ax.hist(numeric_data, bins=min(30, len(set(numeric_data))), alpha=0.7, edgecolor='black')
            ax.set_xlabel(field)
            ax.set_ylabel('Count')

            # Add stats text
            stats = result.get('stats', {})
            if stats.get('mean') is not None:
                stats_text = f"Mean: {stats['mean']:.1f}\nMedian: {stats['median']:.1f}\nStd: {stats['std']:.1f}"
                ax.text(0.75, 0.95, stats_text, transform=ax.transAxes, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        else:
            # Categorical histogram (bar chart)
            from collections import Counter
            counts = Counter(data)
            categories = list(counts.keys())
            values = list(counts.values())

            ax.bar(range(len(categories)), values, alpha=0.7)
            ax.set_xticks(range(len(categories)))
            ax.set_xticklabels(categories, rotation=45, ha='right')
            ax.set_xlabel(field)
            ax.set_ylabel('Count')

        ax.set_title(title or f'Distribution of {field} (n={result["count"]})')

    def _plot_scatter(self, result: Dict[str, Any], title: Optional[str]) -> None:
        """Create scatter plot with interactive popups."""
        self.current_fig, ax = plt.subplots(figsize=self.fig_size, dpi=self.dpi)

        x_data = result['x_data']
        y_data = result['y_data']
        x_field = result['x_field']
        y_field = result['y_field']

        # Create scatter plot with better picker sensitivity
        scatter = ax.scatter(x_data, y_data, alpha=0.6, picker=True, pickradius=10)
        ax.set_xlabel(x_field)
        ax.set_ylabel(y_field)
        ax.set_title(title or f'{y_field} vs {x_field} (n={result["count"]})')

        # Add interactive popup functionality
        if 'pr_numbers' in result:
            self._add_interactive_popup(ax, scatter, x_data, y_data, result['pr_numbers'], x_field, y_field)

        # Add trend line for numeric data
        try:
            x_numeric = [float(x) for x in x_data]
            y_numeric = [float(y) for y in y_data]
            if len(x_numeric) > 1:
                z = np.polyfit(x_numeric, y_numeric, 1)
                p = np.poly1d(z)
                ax.plot(x_numeric, p(x_numeric), "r--", alpha=0.8, label=f'Trend: y={z[0]:.2f}x+{z[1]:.2f}')
                ax.legend()
        except (ValueError, TypeError):
            pass  # Not numeric data

        # Add instruction for user
        if 'pr_numbers' in result:
            ax.text(0.02, 0.98, 'Click points to see PR details\nUse "identify WHERE ..." for tables',
                   transform=ax.transAxes, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5),
                   fontsize=9)

    def _plot_line(self, result: Dict[str, Any], title: Optional[str]) -> None:
        """Create line plot."""
        self.current_fig, ax = plt.subplots(figsize=self.fig_size, dpi=self.dpi)

        x_data = result['x_data']
        y_data = result['y_data']
        x_field = result['x_field']
        y_field = result['y_field']

        ax.plot(x_data, y_data, marker='o', alpha=0.7)
        ax.set_xlabel(x_field)
        ax.set_ylabel(y_field)
        ax.set_title(title or f'{y_field} over {x_field} (n={result["count"]})')

    def _plot_trend(self, result: Dict[str, Any], title: Optional[str]) -> None:
        """Create trend plot."""
        self.current_fig, ax = plt.subplots(figsize=self.fig_size, dpi=self.dpi)

        time_field = result['time_field']

        if 'times' in result:
            # DateTime trend
            times = result['times']
            counts = result['counts']
            ax.plot(times, counts, marker='o', linewidth=2)
            ax.set_xlabel('Time Period')
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        else:
            # Value trend
            values = result['values']
            counts = result['counts']
            ax.plot(values, counts, marker='o', linewidth=2)
            ax.set_xlabel(time_field)

        ax.set_ylabel('Count')
        ax.set_title(title or f'Trend of {time_field} (total={result["total_count"]})')

    def _plot_trend_grouped(self, result: Dict[str, Any], title: Optional[str]) -> None:
        """Create grouped trend plot."""
        self.current_fig, ax = plt.subplots(figsize=self.fig_size, dpi=self.dpi)

        time_field = result['time_field']
        group_by = result['group_by']
        data = result['data']

        for group_name, group_data in data.items():
            if 'times' in group_data:
                ax.plot(group_data['times'], group_data['counts'],
                       marker='o', label=group_name, linewidth=2)
            else:
                ax.plot(group_data['values'], group_data['counts'],
                       marker='o', label=group_name, linewidth=2)

        ax.set_xlabel('Time Period' if 'times' in next(iter(data.values())) else time_field)
        ax.set_ylabel('Count')
        ax.set_title(title or f'Trend of {time_field} by {group_by} (total={result["total_count"]})')
        ax.legend()
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

    def _plot_bar(self, result: Dict[str, Any], title: Optional[str]) -> None:
        """Create bar chart."""
        self.current_fig, ax = plt.subplots(figsize=self.fig_size, dpi=self.dpi)

        categories = result['categories']
        counts = result['counts']
        field = result['field']

        # Limit to top 20 categories if too many
        if len(categories) > 20:
            # Sort by count and take top 20
            sorted_data = sorted(zip(categories, counts), key=lambda x: x[1], reverse=True)
            categories = [x[0] for x in sorted_data[:20]]
            counts = [x[1] for x in sorted_data[:20]]

        bars = ax.bar(range(len(categories)), counts, alpha=0.7)
        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels([str(cat) for cat in categories], rotation=45, ha='right')
        ax.set_xlabel(field)
        ax.set_ylabel('Count')
        ax.set_title(title or f'Distribution of {field} (total={result["total_count"]})')

        # Add value labels on bars
        for i, (bar, count) in enumerate(zip(bars, counts)):
            if count > 0:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.1,
                       f'{count}', ha='center', va='bottom')

    def _plot_bar_grouped(self, result: Dict[str, Any], title: Optional[str]) -> None:
        """Create grouped bar chart."""
        self.current_fig, ax = plt.subplots(figsize=self.fig_size, dpi=self.dpi)

        categories = result['categories']
        groups = result['groups']
        data = np.array(result['data'])
        field = result['field']
        group_by = result['group_by']

        # Limit categories if too many
        if len(categories) > 15:
            categories = categories[:15]
            data = data[:15]

        x = np.arange(len(categories))
        width = 0.8 / len(groups)

        for i, group in enumerate(groups):
            ax.bar(x + i * width, data[:, i], width, label=str(group), alpha=0.7)

        ax.set_xticks(x + width * (len(groups) - 1) / 2)
        ax.set_xticklabels([str(cat) for cat in categories], rotation=45, ha='right')
        ax.set_xlabel(field)
        ax.set_ylabel('Count')
        ax.set_title(title or f'{field} by {group_by} (total={result["total_count"]})')
        ax.legend()

    def _print_stats(self, result: Dict[str, Any]) -> None:
        """Print statistical summary."""
        field = result['field']
        print(f"\nStatistics for {field}:")
        print("=" * 50)

        if 'mean' in result:
            # Numeric statistics
            print(f"Count:  {result['count']}")
            print(f"Mean:   {result['mean']:.2f}")
            print(f"Median: {result['median']:.2f}")
            print(f"Std:    {result['std']:.2f}")
            print(f"Min:    {result['min']:.2f}")
            print(f"Max:    {result['max']:.2f}")
        else:
            # Categorical statistics
            print(f"Count:  {result['count']}")
            print(f"Unique: {result['unique']}")
            if result.get('top'):
                print(f"Most common: {result['top']}")

            if 'value_counts' in result:
                print(f"\nTop values:")
                for value, count in result['value_counts'].items():
                    print(f"  {value}: {count}")

        print(f"\nTotal records: {result['total_count']}")

    def _print_stats_grouped(self, result: Dict[str, Any]) -> None:
        """Print grouped statistical summary."""
        field = result['field']
        group_by = result['group_by']
        data = result['data']

        print(f"\nStatistics for {field} grouped by {group_by}:")
        print("=" * 60)

        for group_name, group_stats in data.items():
            print(f"\n{group_by} = {group_name}:")
            print("-" * 30)

            if 'mean' in group_stats:
                # Numeric statistics
                print(f"  Count:  {group_stats['count']}")
                print(f"  Mean:   {group_stats['mean']:.2f}")
                print(f"  Median: {group_stats['median']:.2f}")
                print(f"  Std:    {group_stats['std']:.2f}")
                print(f"  Min:    {group_stats['min']:.2f}")
                print(f"  Max:    {group_stats['max']:.2f}")
            else:
                # Categorical statistics
                print(f"  Count:  {group_stats['count']}")
                print(f"  Unique: {group_stats['unique']}")
                if group_stats.get('top'):
                    print(f"  Most common: {group_stats['top']}")

        print(f"\nTotal records: {result['total_count']}")

    def save_plot(self, filename: str) -> None:
        """Save current plot to file."""
        if self.current_fig is not None:
            self.current_fig.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"Plot saved to {filename}")
        else:
            print("No plot to save")

    def _add_interactive_popup(self, ax, scatter, x_data, y_data, pr_numbers, x_field, y_field):
        """Add interactive click popup functionality to scatter plot."""

        # Store data for click handler
        self._popup_data = {
            'x_data': x_data,
            'y_data': y_data,
            'pr_numbers': pr_numbers,
            'x_field': x_field,
            'y_field': y_field,
            'ax': ax
        }

        # Remove any existing annotations
        self._current_annotations = []

        def on_pick(event):
            """Handle click events on scatter plot points."""
            print(f"Pick event triggered! Artist: {event.artist}, Indices: {event.ind}")

            if event.artist != scatter:
                print("Not our scatter plot, ignoring")
                return

            # Clear previous annotations
            for annotation in self._current_annotations:
                annotation.remove()
            self._current_annotations.clear()

            # Get clicked point indices
            indices = event.ind

            if len(indices) == 0:
                return

            # For dense areas, collect all nearby points within a small radius
            click_tolerance = 0.05  # 5% of data range
            x_range = max(x_data) - min(x_data) if max(x_data) != min(x_data) else 1
            y_range = max(y_data) - min(y_data) if max(y_data) != min(y_data) else 1

            clicked_x = x_data[indices[0]]
            clicked_y = y_data[indices[0]]

            # Find all points within tolerance
            nearby_indices = []
            for i, (x, y) in enumerate(zip(x_data, y_data)):
                x_dist = abs(x - clicked_x) / x_range if x_range > 0 else 0
                y_dist = abs(y - clicked_y) / y_range if y_range > 0 else 0
                if x_dist <= click_tolerance and y_dist <= click_tolerance:
                    nearby_indices.append(i)

            # Limit to reasonable number for popup
            if len(nearby_indices) > 10:
                nearby_indices = nearby_indices[:10]

            # Create popup text
            if len(nearby_indices) == 1:
                i = nearby_indices[0]
                popup_text = f"PR#{pr_numbers[i]}\n{x_field}: {x_data[i]}\n{y_field}: {y_data[i]}"
                print(f"Creating popup for single PR: {popup_text}")
            else:
                pr_list = [f"PR#{pr_numbers[i]}" for i in nearby_indices]
                if len(pr_list) <= 5:
                    pr_text = ", ".join(pr_list)
                else:
                    pr_text = ", ".join(pr_list[:4]) + f"\n+ {len(pr_list)-4} more..."

                popup_text = f"{len(nearby_indices)} PRs at ({clicked_x}, {clicked_y}):\n{pr_text}"
                print(f"Creating popup for multiple PRs: {popup_text}")

            # Position popup to avoid edges
            popup_x = clicked_x
            popup_y = clicked_y

            # Adjust position if near edges
            x_lim = ax.get_xlim()
            y_lim = ax.get_ylim()

            if popup_x > (x_lim[1] - x_lim[0]) * 0.7 + x_lim[0]:
                h_align = 'right'
                offset_x = -10
            else:
                h_align = 'left'
                offset_x = 10

            if popup_y > (y_lim[1] - y_lim[0]) * 0.7 + y_lim[0]:
                v_align = 'top'
                offset_y = -10
            else:
                v_align = 'bottom'
                offset_y = 10

            # Create annotation
            annotation = ax.annotate(
                popup_text,
                xy=(popup_x, popup_y),
                xytext=(offset_x, offset_y),
                textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.9, edgecolor='black'),
                fontsize=9,
                ha=h_align,
                va=v_align,
                zorder=1000
            )

            self._current_annotations.append(annotation)

            # Refresh the plot
            self.current_fig.canvas.draw()
            self.current_fig.canvas.flush_events()

        # Connect the event handler
        self.current_fig.canvas.mpl_connect('pick_event', on_pick)

        # Also add a fallback click handler for better compatibility
        def on_click(event):
            if event.inaxes != ax:
                return

            print(f"Click event at ({event.xdata}, {event.ydata})")

            # Clear previous annotations
            for annotation in self._current_annotations:
                annotation.remove()
            self._current_annotations.clear()

            if event.xdata is None or event.ydata is None:
                plt.draw()
                return

            # Find closest point manually (fallback if picker doesn't work)
            click_x, click_y = event.xdata, event.ydata
            min_dist = float('inf')
            closest_idx = -1

            # Calculate distance to all points
            for i, (x, y) in enumerate(zip(x_data, y_data)):
                try:
                    dist = ((float(x) - click_x) ** 2 + (float(y) - click_y) ** 2) ** 0.5
                    if dist < min_dist:
                        min_dist = dist
                        closest_idx = i
                except:
                    continue

            # If click is reasonably close to a point (within 10% of plot range)
            x_range = ax.get_xlim()[1] - ax.get_xlim()[0]
            y_range = ax.get_ylim()[1] - ax.get_ylim()[0]
            max_click_dist = min(x_range, y_range) * 0.1

            if closest_idx >= 0 and min_dist < max_click_dist:
                # Create popup for closest point
                popup_text = f"PR#{pr_numbers[closest_idx]}\n{x_field}: {x_data[closest_idx]}\n{y_field}: {y_data[closest_idx]}"

                annotation = ax.annotate(
                    popup_text,
                    xy=(x_data[closest_idx], y_data[closest_idx]),
                    xytext=(10, 10),
                    textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.9, edgecolor='black'),
                    fontsize=9,
                    zorder=1000
                )

                self._current_annotations.append(annotation)
                print(f"Added popup for PR#{pr_numbers[closest_idx]}")

            self.current_fig.canvas.draw()
            self.current_fig.canvas.flush_events()

        self.current_fig.canvas.mpl_connect('button_press_event', on_click)

    def close_plot(self) -> None:
        """Close current plot."""
        if self.current_fig is not None:
            plt.close(self.current_fig)
            self.current_fig = None