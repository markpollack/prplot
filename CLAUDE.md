# PRPlot - Interactive PR Data Analysis CLI

## Project Overview

**PRPlot** is a ROOT/PAW-inspired interactive command-line tool for analyzing GitHub Pull Request data using SQL-style queries. Built for rapid exploratory data analysis with physics-computing ease of use.

## Core Philosophy

- **Single-line queries** for instant insights (ROOT/PAW style)
- **SQL-familiar syntax** for broader accessibility
- **Interactive exploration** with clickable visualizations
- **Clean separation** between data exploration and investigation
- **Physics-grade performance** for iterative analysis workflows

## Architecture

```
prplot/
├── __init__.py          # Package entry point
├── __main__.py          # Module execution entry
├── cli.py               # Interactive REPL with tab completion
├── parser.py            # SQL-style query language parser
├── data_loader.py       # JSON loader with data enrichment
├── query_engine.py      # Query execution and filtering
├── visualizer.py        # Plot generation with matplotlib
└── utils.py            # Helper functions
```

## Key Design Decisions

### 1. **Query Language Choice**
- **Chose**: SQL-style WHERE clauses (`WHERE state = 'open' AND comments > 5`)
- **Over**: ROOT's `name=value` syntax
- **Reason**: Broader familiarity, better complex condition support

### 2. **Interactive Approach**
- **Primary**: `identify WHERE condition` command for investigation
- **Secondary**: Clickable plot points for ad-hoc exploration
- **Fallback**: Export commands for external analysis

### 3. **Data Enrichment Strategy**
- **Computed fields** added at load time (age_days, complexity, activity_score)
- **Categorical bucketing** for easier analysis (time_bucket, complexity levels)
- **Optimized dtypes** for memory efficiency and speed

### 4. **Plot Interaction Model**
- **Clean plots by default** (no cluttered labels)
- **Click to investigate** specific points
- **Popup shows PR# + values** with smart positioning
- **Dense area handling** for overlapping points

## Implementation Highlights

### Query Parser (`parser.py`)
- **pyparsing-based** SQL-style grammar
- **Handles**: comparisons, boolean logic, field references
- **Supports**: dot notation (`labels_assigned.label`)
- **Robust**: handles pyparsing Group objects and nested structures

### Interactive Visualization (`visualizer.py`)
- **Dual event handling**: picker events + fallback click detection
- **Smart positioning**: avoids plot edges, handles dense areas
- **Auto-refresh**: proper canvas drawing for popup updates
- **Matplotlib backend agnostic**: works across different backends

### Data Pipeline (`data_loader.py`)
- **Fast loading**: pandas-optimized JSON processing
- **Rich enrichment**: 15+ computed fields for analysis
- **Type optimization**: categorical and boolean conversions
- **Error resilient**: handles missing/malformed data gracefully

## Development Guidelines

### For Contributors

1. **Follow the single-responsibility principle**: Each module has a clear purpose
2. **Maintain SQL compatibility**: Query syntax should feel natural to SQL users
3. **Preserve physics workflow**: Keep the rapid iteration experience intact
4. **Test interactively**: Development should be done with real PR data

### For Extensions

1. **New plot types**: Add to `visualizer.py` with consistent interface
2. **New query syntax**: Extend `parser.py` grammar carefully
3. **New data sources**: Follow `data_loader.py` enrichment patterns
4. **New export formats**: Add to `cli.py` utility commands

### Testing Strategy

- **Manual testing** with real PR data (primary)
- **Parser unit tests** for query language edge cases
- **Integration testing** via `test_queries.py` script
- **Interactive verification** of plot functionality

## Dependencies & Rationale

### Core Dependencies
- **pandas**: Fast data manipulation, proven in scientific computing
- **matplotlib**: Mature plotting with event handling support
- **pyparsing**: Robust grammar parsing for query language
- **prompt-toolkit**: Professional CLI with autocomplete
- **rich**: Beautiful terminal output for tables

### Why These Choices
- **Matplotlib over Plotly**: Better event handling for interactive features
- **pandas over raw Python**: Performance and expressiveness for data analysis
- **pyparsing over regex**: Maintainable grammar for complex queries
- **prompt-toolkit over readline**: Modern CLI features (autocomplete, history)

## Performance Characteristics

### Data Loading
- **199 PRs**: ~2 seconds (includes enrichment)
- **Memory usage**: ~50MB for enriched dataset
- **Optimization**: Categorical dtypes, computed field caching

### Query Execution
- **Simple filters**: <100ms for WHERE clauses
- **Complex aggregations**: <500ms for groupby operations
- **Plot generation**: 1-3 seconds depending on complexity

### Interactive Response
- **Tab completion**: <50ms for field suggestions
- **Click events**: <100ms for popup display
- **Plot refresh**: <200ms for annotation updates

## Known Limitations

1. **Dataset size**: Designed for thousands, not millions of PRs
2. **Plot types**: Currently 5 plot types, could expand
3. **Export formats**: JSON only, could add CSV/Excel
4. **Query language**: Subset of SQL, not full SQL compatibility
5. **Concurrent plotting**: One plot window at a time

## Future Enhancements

### Short Term
- **More plot types**: violin plots, box plots, heatmaps
- **Export formats**: CSV, Excel, formatted reports
- **Query shortcuts**: saved queries, query history
- **Plot customization**: colors, styles, themes

### Long Term
- **Multiple datasets**: compare repositories
- **Real-time updates**: live PR data feeds
- **Collaborative features**: shared analysis sessions
- **Advanced analytics**: statistical tests, ML insights

## Success Metrics

PRPlot succeeds when:
1. **Physics researchers** feel at home with the query interface
2. **Development teams** use it for regular PR triage
3. **Data analysts** prefer it over Excel for GitHub data
4. **Contributors** can add features without architectural changes
5. **Users** discover insights they wouldn't find otherwise

## Integration Notes

### For Spring AI PR Analysis
This tool was specifically designed for analyzing Spring AI project PRs with:
- **Label-based categorization** (MCP, vector store, etc.)
- **Age-based triage** for identifying stale PRs
- **Activity correlation** analysis
- **Contributor pattern recognition**

### For Other Projects
The tool is generic and works with any GitHub PR JSON export that includes:
- Basic PR fields (number, title, state, created_at, etc.)
- Comment counts and reaction data
- Label information (optional but recommended)
- User/author information

---

*PRPlot brings the rapid exploratory data analysis experience of ROOT/PAW to modern GitHub workflow analysis, making PR data as easy to explore as particle physics datasets.*