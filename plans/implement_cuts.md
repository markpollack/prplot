# Implementation Plan: Named Cuts

## Goal

Add ROOT/PAW-inspired named cuts to prplot — reusable aliases for WHERE clauses
that can be referenced by `$name` in any command and composed with AND/OR/NOT.

```
cut trusted author IN ('sdeleuze', 'markpollack', 'tzolov')
cut fresh created_at_dt > now-7d
identify $trusted AND $fresh
hist age_days WHERE $trusted
```

## Background

See `plans/research/supporting_docs/` for ROOT TCut and PAW NT/CUT reference
material that informed this design.

---

## Changes by File

### 1. `prplot/cuts.py` (new)

A `CutRegistry` class that stores and resolves named cuts.

```python
class CutRegistry:
    """Stores named cuts as raw expression strings."""

    def __init__(self):
        self._cuts: dict[str, str] = {}   # name → expression string

    def define(self, name: str, expression: str) -> None:
        """Define or overwrite a cut."""
        self._cuts[name] = expression

    def remove(self, name: str) -> None:
        """Remove a cut. Raises KeyError if not found."""
        del self._cuts[name]

    def list_all(self) -> dict[str, str]:
        """Return all cuts as {name: expression}."""
        return dict(self._cuts)

    def resolve(self, text: str) -> str:
        """Replace all $name references in text with parenthesized expressions.

        E.g. "$trusted AND $fresh"
           → "(author IN ('sdeleuze','markpollack','tzolov')) AND (created_at_dt > now-7d)"

        Raises ValueError for undefined $references.
        """
```

**Resolution algorithm:**
- Regex scan for `\$([a-zA-Z_]\w*)` in the input string
- For each match, look up name in `_cuts`; raise `ValueError` if missing
- Replace `$name` with `(<expression>)` (parenthesized to preserve precedence)
- Single pass is sufficient — no recursive cut references (out of scope)

**Persistence (optional, deferred):**
- `save(path)` / `load(path)` writing JSON `{"cuts": {"name": "expr"}}` to `~/.prplot_cuts`
- Can be added later without changing the core API

### 2. `prplot/cli.py`

#### 2a. Initialization

Add `CutRegistry` to `PRAnalysisCLI.__init__`:

```python
from .cuts import CutRegistry
self.cut_registry = CutRegistry()
```

#### 2b. Command routing in `run()`

Add three new command branches in the main `while True` loop, after the
existing `elif` chain and before the fallthrough to `_execute_query`:

| Input pattern | Handler |
|---------------|---------|
| `cut <name> <expression>` | `self._handle_cut_define(query)` |
| `uncut <name>` | `self._handle_cut_remove(query)` |
| `cuts` | `self._handle_cuts_list()` |

Detection is simple string prefix matching (same pattern as `identify`, `save`,
`export`, `fields`, etc.):

```python
elif query.lower() == 'cuts':
    self._handle_cuts_list()
elif query.lower().startswith('cut '):
    self._handle_cut_define(query)
elif query.lower().startswith('uncut '):
    self._handle_cut_remove(query)
```

**Important**: place `cuts` before `cut ` in the elif chain so `cuts` (list)
doesn't match `cut ` (define).

#### 2c. Cut resolution hook

Before passing any command string to the parser or to `_handle_identify`,
resolve `$name` references:

```python
# In the main loop, after getting `query` from input and before dispatch:
if '$' in query:
    try:
        query = self.cut_registry.resolve(query)
    except ValueError as e:
        self.console.print(f"[red]Cut error: {e}[/red]")
        continue
```

This is a single insertion point — all downstream code (parser, query engine,
identify handler) receives fully expanded text with no `$` references.

#### 2d. Handler implementations

**`_handle_cut_define(query)`**:
- Parse: split on first two spaces → `"cut"`, `name`, `rest`
- Validate name matches `[a-zA-Z_]\w*`
- Store: `self.cut_registry.define(name, rest)`
- Print confirmation: `"Cut '$name' defined: rest"`

**`_handle_cut_remove(query)`**:
- Parse: `query.split()[1]` → name
- `self.cut_registry.remove(name)`
- Print: `"Cut '$name' removed"`

**`_handle_cuts_list()`**:
- If empty: `"No cuts defined"`
- Otherwise: Rich table with Name and Expression columns

#### 2e. Tab completion

Add to `PRCompleter`:
- After commands, include `cut`, `uncut`, `cuts` in `self.commands`
- When text contains `$`, complete with defined cut names from the registry
  (pass registry reference to completer)

### 3. `prplot/parser.py`

**No changes needed.** Cut resolution happens in cli.py *before* the parser
sees the string. The parser receives fully expanded WHERE expressions identical
to what a user would type manually. This keeps the parser simple and avoids
grammar changes.

### 4. `prplot/query_engine.py`

**No changes needed.** The query engine evaluates the parsed condition tree,
which is already fully resolved.

### 5. Help text

Update `_show_help()` in cli.py to add a Cuts section:

```
[blue]Cut Commands:[/blue]
  cut <name> <expression>              - Define a named cut
  uncut <name>                         - Remove a named cut
  cuts                                 - List all defined cuts

[blue]Using Cuts:[/blue]
  identify $trusted_authors
  hist age_days WHERE $trusted AND $recent
  plot age_days vs comment_count WHERE $active OR $stale
```

---

## Test Plan

### Unit tests: `tests/test_cuts.py` (new)

Test `CutRegistry` in isolation:

| Test | Assertion |
|------|-----------|
| `test_define_and_resolve` | `$c` → `(x > 1)` |
| `test_resolve_multiple` | `$a AND $b` → `(expr_a) AND (expr_b)` |
| `test_resolve_undefined_raises` | `$nope` → `ValueError` |
| `test_remove` | define, remove, resolve → `ValueError` |
| `test_overwrite` | define twice, resolve gets latest |
| `test_list_all` | returns dict of all cuts |
| `test_no_recursive` | `$a` containing `$b` stays literal (single pass) |

### Integration tests: `tests/test_integration.py` (extend)

Add to existing pexpect tests:

| Test | Commands | Assert |
|------|----------|--------|
| `test_cut_define_and_use` | `cut open state = "open"` then `identify $open` | All 5 PR numbers appear |
| `test_cut_compose` | Define `$open` and `$author`, then `identify $open AND $author` | Only matching PRs |
| `test_cuts_list` | `cut x ...` then `cuts` | Table shows name and expression |
| `test_uncut` | `cut x ...`, `uncut x`, `cuts` | "No cuts defined" |
| `test_undefined_cut_error` | `identify $nope` | Error message in output |

---

## Execution Order

1. Create `prplot/cuts.py` with `CutRegistry`
2. Write `tests/test_cuts.py` unit tests, verify they pass
3. Wire into `cli.py`: commands, resolution hook, help text, tab completion
4. Extend `tests/test_integration.py` with pexpect cut tests
5. Run full test suite (`pytest tests/ -v`)

---

## Out of Scope (Future)

- **Persistence**: Save/load cuts to `~/.prplot_cuts` across sessions
- **Recursive cuts**: `$a` referencing `$b` in its expression
- **Cut from file**: `cut load mycuts.json`
- **NOT on cuts**: Currently works via `NOT $name` in the WHERE clause because
  the parser already supports `NOT`; no extra work needed
