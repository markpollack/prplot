# prplot - PR Analysis CLI Tool

**One-line commands to explore GitHub PR data** - inspired by ROOT/PAW but with SQL syntax.

```bash
$ prplot all_prs_labeled.json

prplot> identify comments > 10
prplot> plot comments vs age_days where age_days > 90 and comments > 5
prplot> bar author
prplot> save analysis.png
```

## Quick Start

### For Development
```bash
git clone https://github.com/markpollack/prplot.git
cd prplot
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m prplot all_prs_labeled.json  # Uses included sample data
```

### For End Users
```bash
pip install git+https://github.com/markpollack/prplot.git
prplot your_data.json
```

> **Note**: Examples below use Spring AI PR data where all PRs happen to be open. For mixed datasets with open/closed PRs, use `WHERE state = 'open'` or `WHERE state = 'closed'` to filter as needed.

## Refreshing PR Data

prplot analyzes GitHub PR data exported as JSON. Use the [github-collector](https://github.com/spring-ai-community/github-collector) CLI to fetch fresh data.

### Prerequisites

1. **GitHub Token**: Export `GITHUB_TOKEN` environment variable
2. **Build github-collector** (one-time):
   ```bash
   cd ~/community/github-collector
   mvn clean package -DskipTests
   ```

### Quick Refresh

```bash
export GITHUB_TOKEN=your_token_here

java -jar ~/community/github-collector/github-collector-cli/target/github-collector-cli-1.0.0-SNAPSHOT.jar \
    --repo spring-projects/spring-ai \
    --type prs \
    --pr-state open \
    --single-file \
    -o all_prs.json

# Then run prplot
python -m prplot all_prs.json
```

### Incremental Updates

Add new PRs without re-fetching everything:

```bash
java -jar ~/community/github-collector/github-collector-cli/target/github-collector-cli-1.0.0-SNAPSHOT.jar \
    --repo spring-projects/spring-ai \
    --type prs \
    --pr-state open \
    --single-file \
    --incremental \
    --no-clean \
    -o all_prs.json
```

### Collection Options

| Option | Description |
|--------|-------------|
| `--pr-state` | `open`, `closed`, `merged`, or `all` |
| `--single-file` | Output to single consolidated file |
| `-o, --output` | Output file path |
| `--incremental` | Skip already collected PRs |
| `--no-clean` | Keep existing data, append new |
| `--max-issues N` | Limit total PRs collected |
| `--dry-run` | Preview without writing |

### Labels

PRs include GitHub labels in the `labels` field (list of `{name, color, description}` objects). The enriched `label_names` field extracts just the name strings for easy querying:

```bash
prplot> bar label_names
prplot> identify label_names CONTAINS 'bug'
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
- `WHERE age_days > 90 AND comment_count > 5` → Multiple conditions
- `WHERE label_names CONTAINS 'bug'` → Text search
- `WHERE author LIKE '%spring%'` → Pattern matching
- `WHERE created_at_dt > now-30d` → Relative date filtering

**Investigation:**
- **Click any plot point** → See PR# and details in popup
- `identify comments > 10` → Show matching PRs in rich tables with clickable URLs
- `export WHERE condition TO file.json` → Save filtered data

## 5-Minute Tutorial

### 1. **See What Data You Have**
```bash
prplot> fields
# Shows all available columns: age_days, state, comment_count, label_names, etc.
```

### 2. **Basic Distributions**
```bash
# How old are the PRs?
prplot> hist age_days

# What's the mix of open vs closed?
prplot> bar state

# Which authors are most active?
prplot> bar author
```

### 3. **Filter with WHERE**
```bash
# PRs with lots of activity
prplot> hist comment_count where comment_count > 5

# Older PRs only
prplot> hist age_days where age_days > 90

# PRs created in the last 30 days
prplot> hist age_days where created_at_dt > now-30d

# High-activity old PRs
prplot> bar author where age_days > 90 and comment_count > 3
```

### 4. **Correlations**
```bash
# Do older PRs get more comments?
prplot> plot age_days vs comment_count

# Focus on active PRs
prplot> plot age_days vs comment_count where comment_count > 2

# Activity vs age patterns
prplot> plot activity_score vs age_days where age_days > 60
```

### 5. **Time Trends**
```bash
# PR creation over time
prplot> trend created_at_dt

# Broken down by author
prplot> trend created_at_dt by author

# Focus on older PRs
prplot> trend created_at_dt where age_days > 90
```

### 6. **Quick Stats**
```bash
# Summary of comment activity
prplot> stats comment_count

# Broken down by state
prplot> stats comment_count by state

# Age analysis by complexity
prplot> stats age_days by complexity
```

### 7. **Identify Specific PRs**
```bash
# Find high-activity PRs
prplot> identify comment_count > 10

# Find old open PRs
prplot> identify state = 'open' and age_days > 200

# Find recent activity
prplot> identify age_days < 30 and activity_score > 10

# Find PRs from specific contributors
prplot> identify author in ('sunyuhan1998', 'quaff', 'wilocu')

# Find PRs updated in the last week
prplot> identify updated_at_dt > now-7d

# Results shown in table with clickable "View PR" links
```

### 8. **Export Results**
```bash
# Save current plot
prplot> save pr_analysis.png

# Export filtered data
prplot> export where label_names CONTAINS 'MCP' to mcp_prs.json

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
prplot> plot comment_count vs age_days where state = 'open'
prplot> hist activity_score where state = 'open'
prplot> stats comment_count by author
```

### **Label Deep Dive**
```bash
prplot> bar label_names
prplot> trend created_at_dt by author where age_days < 180
prplot> stats age_days by author where state = 'open'
```

### **Complexity Patterns**
```bash
prplot> bar complexity
prplot> plot complexity vs comment_count where state = 'open'
prplot> stats age_days by complexity where state = 'open'
```

## Command Reference

### Plot Commands

| Command | Description | Example |
|---------|-------------|---------|
| `HIST field` | Histogram of field values | `hist age_days` |
| `PLOT x [VS y]` | Scatter plot or line plot | `plot comments vs age_days` |
| `TREND field [BY group]` | Time series trend | `trend created_at_dt by author` |
| `BAR field [BY group]` | Bar chart | `bar author` |
| `STATS field [BY group]` | Statistical summary | `stats comments by state` |

### WHERE Clause Syntax

All plot commands support SQL-style WHERE clauses:

```sql
-- Equality and comparison
WHERE state = 'open'
WHERE age_days > 90
WHERE comment_count >= 5

-- Boolean operators
WHERE state = 'open' AND comment_count > 5
WHERE age_days > 180 OR activity_score > 10

-- String matching
WHERE author LIKE '%spring%'
WHERE label_names CONTAINS 'bug'

-- List membership (IN operator)
WHERE state IN ('open', 'closed')
WHERE complexity IN ('high', 'medium')
WHERE author IN ('sunyuhan1998', 'quaff', 'wilocu')

-- Relative dates (Grafana-style)
WHERE created_at_dt > now-30d
WHERE updated_at_dt < now-6M

-- Absolute dates (quoted ISO strings)
WHERE created_at_dt > '2025-01-01'
WHERE created_at_dt > '2025-06-15T00:00:00'
```

### Date Filtering

prplot supports Grafana-style relative date literals for filtering by date fields (`created_at_dt`, `updated_at_dt`, `closed_at_dt`). No quotes needed.

**Relative dates** (`now-<amount><unit>`):

| Unit | Meaning | Example |
|------|---------|---------|
| `d` | days | `now-30d` — 30 days ago |
| `w` | weeks | `now-2w` — 2 weeks ago |
| `M` | months | `now-6M` — 6 months ago |
| `y` | years | `now-1y` — 1 year ago |

```bash
# PRs created in the last 30 days
prplot> hist age_days where created_at_dt > now-30d

# PRs not updated in 6+ months
prplot> identify updated_at_dt < now-6M

# PRs from the last year
prplot> trend created_at_dt where created_at_dt > now-1y
```

**Absolute dates** (quoted ISO strings):
```bash
prplot> identify created_at_dt > '2025-01-01'
prplot> hist age_days where created_at_dt > '2025-06-15'
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
- `label_count` - Number of GitHub labels

### Label Fields
- `label_names` - List of GitHub label name strings

### Activity Fields
- `comment_count` - Number of comments
- `activity_score` - Same as comment_count
- `author` - PR author login
- `author_login` - PR author login (alias)

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
prplot> plot comment_count vs age_days where state = 'open'
[Scatter plot with trend line]

prplot> # Time trends by author
prplot> trend created_at_dt by author
[Multi-line time series plot]

prplot> # Export data for further analysis
prplot> export where label_names CONTAINS 'MCP' to mcp_prs.json
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
      "author": {"login": "username", "name": "Full Name"},
      "comments": [{"author": {"login": "..."}, "body": "...", "created_at": "..."}],
      "labels": [{"name": "bug", "color": "d73a4a", "description": "..."}]
      // ... other fields
    }
  ]
}
```

## Advanced Features

### Tab Completion
- Field names, commands, and operators auto-complete
- **Nested field completion**: Type a dict column name + `.` for subfield suggestions
- Context-aware suggestions based on field types
- Sample values for categorical fields
- Smart completion for nested objects

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

### **HIST - Distributions & Histograms**
```bash
# Basic age distribution
hist age_days

# Comment activity distribution
hist comment_count

# Filter for active PRs only
hist age_days where comment_count > 5

# Focus on older PRs
hist comment_count where age_days > 90 and comment_count > 0
```

### **PLOT - Interactive Scatter Plots**
```bash
# Age vs comment correlation
plot age_days vs comment_count

# Activity score over time
plot age_days vs activity_score

# High-activity subset (click points to see PR#!)
plot age_days vs comment_count where comment_count > 5

# PRs created in the last 6 months
plot age_days vs comment_count where created_at_dt > now-6M
```

### **BAR - Category Breakdowns**
```bash
# Author distribution
bar author

# Age category breakdown
bar time_bucket

# Authors for active PRs only
bar author where comment_count > 3

# Complexity distribution for older PRs
bar complexity where age_days > 90
```

### **TREND - Time Series Analysis**
```bash
# PR creation over time
trend created_at_dt

# Creation trends by author
trend created_at_dt by author

# Focus on recent activity
trend created_week where age_days < 120

# Monthly patterns by complexity
trend created_month by complexity where age_days > 30
```

### **STATS - Statistical Summaries**
```bash
# Overall comment statistics
stats comment_count

# Age breakdown by complexity
stats age_days by complexity

# Activity analysis by author
stats activity_score by author

# Comment patterns for older PRs
stats comment_count by time_bucket where age_days > 60
```

### **IDENTIFY - Find Specific PRs**
```bash
# High-activity PRs
identify comment_count > 10

# Old PRs with ongoing discussion
identify age_days > 200 and comment_count > 3

# Recent high-engagement PRs
identify age_days < 60 and activity_score > 15

# Label-specific investigation
identify label_names contains 'bug' and comment_count > 2

# Alternative WHERE syntax (both forms work identically)
identify age_days where age_days > 90 and comments > 5

# Boolean field queries (case-insensitive)
identify soft_approval_detected = true
identify is_draft = false

# Multiple value matching with IN operator
identify author in ('sunyuhan1998', 'quaff', 'wilocu')
identify state in ('open', 'closed')

# Date-based filtering
identify created_at_dt > now-30d
identify updated_at_dt < now-6M
```

### **EXPORT & SAVE - Data Export**
```bash
# Export high-activity PRs
export where comment_count > 5 to active_prs.json

# Export old PRs with discussion
export where age_days > 180 and comment_count > 2 to old_active_prs.json

# Export recent PRs
export where created_at_dt > now-30d to recent_prs.json

# Save current plot
save correlation_analysis.png
```

### **Tab Completion Examples**
```bash
# Type and press TAB for completions:
plot au<TAB>            # → author, author_login
hist com<TAB>           # → comment_count, comments, complexity
```

### **Field Reference**
**Computed Fields Available:**
- `age_days`, `days_since_update` - Time calculations
- `time_bucket` - "< 1 month", "1-3 months", etc.
- `complexity` - "low", "medium", "high"
- `comment_count` - Number of comments
- `activity_score` - Same as comment_count
- `label_count` - Number of labels
- `label_names` - List of label name strings
- `author` - PR author login

## Dependencies

- `pandas` - Data manipulation
- `matplotlib` / `seaborn` - Plotting
- `pyparsing` - Query parsing
- `prompt-toolkit` - Interactive CLI
- `rich` - Beautiful terminal output

## License

MIT License - see LICENSE file for details.