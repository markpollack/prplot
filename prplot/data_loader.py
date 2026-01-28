"""
Data loader for PR analysis with computed fields and indexing.
"""

import json
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, List


class PRDataLoader:
    """Loads PR data from JSON and enriches with computed fields for fast querying."""

    def __init__(self, json_file: str):
        """Initialize loader with PR data file."""
        self.json_file = json_file
        self.df = None
        self._load_and_enrich()

    def _load_and_enrich(self):
        """Load JSON data and add computed fields."""
        print(f"Loading PR data from {self.json_file}...")

        with open(self.json_file, 'r') as f:
            data = json.load(f)

        # Convert to DataFrame
        self.df = pd.DataFrame(data['prs'])

        print(f"Loaded {len(self.df)} PRs")

        # Add computed fields
        self._add_time_fields()
        self._add_complexity_fields()
        self._add_label_fields()
        self._add_activity_fields()

        # Optimize data types
        self._optimize_dtypes()

        print("Data enrichment complete")

    def _add_time_fields(self):
        """Add time-based computed fields."""
        now = datetime.now(timezone.utc)

        # Convert timestamps to datetime (assume UTC if no timezone info)
        self.df['created_at_dt'] = pd.to_datetime(self.df['created_at'], utc=True)
        self.df['updated_at_dt'] = pd.to_datetime(self.df['updated_at'], utc=True)
        self.df['closed_at_dt'] = pd.to_datetime(self.df['closed_at'], utc=True)

        # Age calculations
        self.df['age_days'] = (now - self.df['created_at_dt']).dt.days
        self.df['days_since_update'] = (now - self.df['updated_at_dt']).dt.days

        # Time buckets
        def time_bucket(days):
            if days < 30:
                return "< 1 month"
            elif days < 90:
                return "1-3 months"
            elif days < 180:
                return "3-6 months"
            elif days < 365:
                return "6-12 months"
            else:
                return "> 1 year"

        self.df['time_bucket'] = self.df['age_days'].apply(time_bucket)

        # Extract date components for grouping
        self.df['created_year'] = self.df['created_at_dt'].dt.year
        self.df['created_month'] = self.df['created_at_dt'].dt.month
        self.df['created_week'] = self.df['created_at_dt'].dt.isocalendar().week

    def _add_complexity_fields(self):
        """Add complexity estimation fields."""
        # Body length as complexity proxy
        self.df['body_length'] = self.df['body'].fillna('').str.len()

        # Label count from labels list
        self.df['label_count'] = self.df['labels'].apply(
            lambda x: len(x) if isinstance(x, list) else 0
        )

        # Complexity estimate based on multiple factors
        def complexity_estimate(row):
            score = 0
            if row['body_length'] > 2000:
                score += 2
            elif row['body_length'] > 500:
                score += 1

            if row['label_count'] > 3:
                score += 1

            if score >= 3:
                return "high"
            elif score >= 1:
                return "medium"
            else:
                return "low"

        self.df['complexity'] = self.df.apply(complexity_estimate, axis=1)

    def _add_label_fields(self):
        """Add label-related fields."""
        # Extract label names from labels list (github-collector schema: [{name, color, description}])
        def extract_label_names(labels):
            if not isinstance(labels, list):
                return []
            return [label.get('name', '') for label in labels]

        self.df['label_names'] = self.df['labels'].apply(extract_label_names)

    def _add_activity_fields(self):
        """Add activity and engagement fields."""
        # comments is a list of comment objects — compute count
        self.df['comment_count'] = self.df['comments'].apply(
            lambda x: len(x) if isinstance(x, list) else 0
        )

        # Activity score based on comment count
        self.df['activity_score'] = self.df['comment_count']

        # Author login extracted from author dict
        self.df['author_login'] = self.df['author'].apply(
            lambda x: x.get('login', '') if isinstance(x, dict) else ''
        )
        # Overwrite author column with login string for easy querying
        self.df['author'] = self.df['author_login']

        # Draft status
        self.df['is_draft'] = self.df['draft'].fillna(False)

    def _optimize_dtypes(self):
        """Optimize DataFrame data types for memory efficiency."""
        # Convert categorical fields (only if they contain strings/simple types)
        categorical_fields = ['state', 'time_bucket', 'complexity', 'author']
        for field in categorical_fields:
            if field in self.df.columns:
                try:
                    sample_vals = self.df[field].dropna().head(10)
                    if all(isinstance(v, (str, type(None))) for v in sample_vals):
                        self.df[field] = self.df[field].astype('category')
                except:
                    pass

        # Convert boolean fields
        bool_fields = ['is_draft']
        for field in bool_fields:
            if field in self.df.columns:
                try:
                    self.df[field] = self.df[field].astype('bool')
                except:
                    pass

    def get_field_info(self) -> Dict[str, Any]:
        """Return information about available fields for tab completion."""
        fields = {}

        for col in self.df.columns:
            dtype = str(self.df[col].dtype)

            try:
                unique_count = self.df[col].nunique()
            except:
                unique_count = 0

            try:
                if unique_count < 20 and unique_count > 0:
                    sample_values = []
                    for val in self.df[col].dropna().head(3):
                        if isinstance(val, (str, int, float, bool)) or val is None:
                            sample_values.append(val)
                        else:
                            sample_values.append(str(val)[:50])
                else:
                    sample_values = []
            except:
                sample_values = []

            fields[col] = {
                'type': dtype,
                'unique_values': unique_count,
                'sample_values': sample_values
            }

        return fields

    def get_data(self) -> pd.DataFrame:
        """Return the enriched DataFrame."""
        return self.df
