# prplot - PR Analysis CLI Tool

**One-line commands to explore GitHub PR data** - inspired by ROOT/PAW but with SQL syntax.

```bash
$ prplot all_prs_labeled.json

prplot> hist age_days
prplot> plot comments vs age_days where state = 'open'
prplot> bar primary_label
prplot> save analysis.png
```

## Quick Start

```bash
# One-time setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Daily usage
source venv/bin/activate  # if not already active
python -m prplot all_prs_labeled.json
```

## Supported Plots & Queries

**Plot Types:**
- `hist field` → Histograms & distributions
- `plot x vs y` → Interactive scatter plots with clickable points
- `bar category` → Bar charts & breakdowns
- `trend time [by group]` → Time series analysis
- `stats field [by group]` → Statistical summaries
- `identify WHERE condition` → Find specific PRs in tables

**Filtering:**
- `WHERE state = 'open'` → SQL-style conditions
- `WHERE age_days > 90 AND comments > 5` → Multiple conditions
- `WHERE primary_label CONTAINS 'vector'` → Text search
- `WHERE author LIKE '%spring%'` → Pattern matching

**Investigation:**
- **Click any plot point** → See PR# and details in popup
- `identify comments > 10` → Show matching PRs in rich tables
- `export WHERE condition TO file.json` → Save filtered data

## 5-Minute Tutorial

### 1. **See What Data You Have**
```bash
prplot> fields
# Shows all available columns: age_days, state, comments, primary_label, etc.
```

### 2. **Basic Distributions**
```bash
# How old are the PRs?
prplot> hist age_days

# What's the mix of open vs closed?
prplot> bar state

# Which labels are most common?
prplot> bar primary_label
```

### 3. **Filter with WHERE**
```bash
# Only look at open PRs
prplot> hist age_days where state = 'open'

# PRs with lots of activity
prplot> hist comments where comments > 5

# Recent PRs only
prplot> bar primary_label where age_days < 30
```

### 4. **Correlations**
```bash
# Do older PRs get more comments?
prplot> plot age_days vs comments

# Just for open PRs
prplot> plot age_days vs comments where state = 'open'

# Activity vs age
prplot> plot activity_score vs age_days where state = 'open'
```

### 5. **Time Trends**
```bash
# PR creation over time
prplot> trend created_at_dt

# Broken down by label type
prplot> trend created_at_dt by primary_label

# Recent activity only
prplot> trend created_at_dt where age_days < 90
```

### 6. **Quick Stats**
```bash
# Summary of comment activity
prplot> stats comments

# Broken down by state
prplot> stats comments by state

# Age analysis by complexity
prplot> stats age_days by complexity
```

### 7. **Identify Specific PRs**
```bash
# Find high-activity PRs
prplot> identify comments > 10

# Find old open PRs
prplot> identify state = 'open' and age_days > 200

# Find recent activity
prplot> identify age_days < 30 and activity_score > 10
```

### 8. **Export Results**
```bash
# Save current plot
prplot> save pr_analysis.png

# Export filtered data
prplot> export where primary_label = 'MCP' to mcp_prs.json

# All old open PRs
prplot> export where state = 'open' and age_days > 180 to stale_prs.json
```

## Common Analysis Patterns

### **Triage by Age**
```bash
prplot> hist age_days where state = 'open'
prplot> bar time_bucket where state = 'open'
prplot> export where state = 'open' and age_days > 365 to very_old_prs.json
```

### **Activity Analysis**
```bash
prplot> plot comments vs age_days where state = 'open'
prplot> hist activity_score where state = 'open'
prplot> stats comments by primary_label
```

### **Label Deep Dive**
```bash
prplot> bar primary_label
prplot> trend created_at_dt by primary_label where age_days < 180
prplot> stats age_days by primary_label where state = 'open'
```

### **Complexity Patterns**
```bash
prplot> bar complexity
prplot> plot complexity vs comments where state = 'open'
prplot> stats age_days by complexity where state = 'open'
```

## Command Reference

### Plot Commands

| Command | Description | Example |
|---------|-------------|---------|
| `HIST field` | Histogram of field values | `hist age_days` |
| `PLOT x [VS y]` | Scatter plot or line plot | `plot comments vs age_days` |
| `TREND field [BY group]` | Time series trend | `trend created_at_dt by primary_label` |
| `BAR field [BY group]` | Bar chart | `bar primary_label` |
| `STATS field [BY group]` | Statistical summary | `stats comments by state` |

### WHERE Clause Syntax

All plot commands support SQL-style WHERE clauses:

```sql
-- Equality and comparison
WHERE state = 'open'
WHERE age_days > 90
WHERE comments >= 5

-- Boolean operators
WHERE state = 'open' AND comments > 5
WHERE age_days > 180 OR total_reactions > 10

-- String matching
WHERE author LIKE '%spring%'
WHERE primary_label CONTAINS 'vector'

-- List membership
WHERE state IN ('open', 'closed')
WHERE complexity IN ('high', 'medium')
```

### Utility Commands

| Command | Description |
|---------|-------------|
| `fields` | Show all available fields with types |
| `help` | Show command help |
| `save filename.png` | Save current plot to file |
| `export WHERE ... TO file.json` | Export filtered data |
| `quit` / `exit` | Exit the CLI |

## Enriched Data Fields

The tool automatically enriches your PR data with computed fields:

### Time Fields
- `age_days` - Days since PR creation
- `days_since_update` - Days since last update
- `time_bucket` - Categorized age ("< 1 month", "1-3 months", etc.)
- `created_year`, `created_month`, `created_week` - Date components

### Complexity Fields
- `body_length` - Length of PR description
- `complexity` - Estimated complexity ("low", "medium", "high")
- `github_label_count` - Number of GitHub labels
- `assigned_label_count` - Number of machine-assigned labels

### Label Fields
- `assigned_label_names` - List of assigned label names
- `github_label_names` - List of GitHub label names
- `primary_label` - Highest confidence assigned label

### Activity Fields
- `total_reactions` - Sum of all reaction types
- `activity_score` - Comments + reactions
- `author` - PR author username

## Example Analysis Session

```bash
prplot> # Start with basic exploration
prplot> fields
[Shows all available fields with types]

prplot> # Look at PR age distribution
prplot> hist age_days
[Histogram showing distribution of PR ages]

prplot> # Focus on open PRs only
prplot> hist age_days where state = 'open'
[Histogram of open PR ages]

prplot> # Correlation analysis
prplot> plot comments vs age_days where state = 'open'
[Scatter plot with trend line]

prplot> # Time trends by category
prplot> trend created_at_dt by primary_label
[Multi-line time series plot]

prplot> # Export data for further analysis
prplot> export where primary_label = 'MCP' to mcp_prs.json
Exported 23 PRs to mcp_prs.json

prplot> # Save visualization
prplot> save pr_age_analysis.png
Plot saved to pr_age_analysis.png
```

## Data Format

The tool expects JSON files with the structure:

```json
{
  "prs": [
    {
      "number": 4396,
      "title": "fix: mcp server registration tools failed",
      "state": "open",
      "created_at": "2025-09-15T16:43:43Z",
      "labels_assigned": [
        {"label": "MCP", "confidence": 1.0}
      ],
      // ... other GitHub API fields
    }
  ]
}
```

## Advanced Features

### Tab Completion
- Field names, commands, and operators auto-complete
- Context-aware suggestions based on field types
- Sample values for categorical fields

### Command History
- Previous commands saved across sessions
- Use arrow keys to navigate history
- History stored in `~/.prplot_history`

### Auto-Plot Selection
- Numeric fields → histograms or scatter plots
- Categorical fields → bar charts
- DateTime fields → trend lines
- Mixed types → appropriate visualizations

### Statistical Overlays
- Automatic trend lines for scatter plots
- Summary statistics in histogram text boxes
- Value labels on bar charts

## Performance Notes

- Data is loaded once at startup and cached in memory
- Pandas DataFrames used for fast filtering and aggregation
- Optimized data types for memory efficiency
- Field indexing for quick lookups

## Complete Examples Reference

### **Quick Data Exploration**
```bash
# Basic distributions
hist age_days                    # How old are PRs?
bar state                        # Open vs closed breakdown
bar primary_label                # Most common labels
bar time_bucket                  # Age categories

# Filter with WHERE
hist age_days where state = 'open'
bar primary_label where age_days < 90
```

### **Interactive Analysis**
```bash
# Scatter plots with clickable points
plot comments vs age_days where state = 'open'
plot total_reactions vs comments
plot activity_score vs age_days

# Click any point → See PR# and details!
```

### **Time Series Analysis**
```bash
# PR creation trends
trend created_at_dt
trend created_at_dt by primary_label
trend created_at_dt by state where age_days < 180
```

### **Statistical Deep Dives**
```bash
# Summary statistics
stats comments
stats age_days by state
stats activity_score by complexity
stats comments by primary_label
```

### **Investigation & Export**
```bash
# Find specific PRs
identify comments > 10
identify age_days > 200 and state = 'open'
identify primary_label contains 'MCP'

# Export for further analysis
export where state = 'open' and age_days > 180 to stale_prs.json
export where comments > 5 to active_prs.json
save correlation_plot.png
```

### **Advanced Queries**
```bash
# Complex conditions
plot age_days vs comments where state = 'open' and complexity = 'high'
bar primary_label where created_year = 2024 and comments > 2
stats age_days by author where comments > 0
trend created_week by state where age_days < 90
```

### **Field Reference**
**Computed Fields Available:**
- `age_days`, `days_since_update` - Time calculations
- `time_bucket` - "< 1 month", "1-3 months", etc.
- `complexity` - "low", "medium", "high"
- `activity_score` - comments + reactions
- `primary_label` - Main assigned label
- `author` - PR creator
- `total_reactions` - Sum of all reaction types

## Dependencies

- `pandas` - Data manipulation
- `matplotlib` / `seaborn` - Plotting
- `pyparsing` - Query parsing
- `prompt-toolkit` - Interactive CLI
- `rich` - Beautiful terminal output

## License

MIT License - see LICENSE file for details.