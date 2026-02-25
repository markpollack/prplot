# Cuts Feature Design Notes

## Inspiration

Both ROOT and PAW provide **named, reusable selection criteria** (cuts) that
can be composed with logical operators and applied to any plot or query command.

### ROOT's TCut

```cpp
TCut quality  = "chi2 < 10";
TCut signal   = "mass > 80 && mass < 120";
tree->Draw("pt", quality && signal);
```

### PAW's Named Cuts

```
CUT $1 step=15
CUT $2 grade>4
ntuple/plot 10.division $1.and.$2
```

## Proposed prplot Syntax

### Defining Cuts

```
cut trusted_authors author IN ('sdeleuze', 'markpollack', 'tzolov')
cut recent created_at_dt > now-30d
cut active comment_count > 5
cut stale age_days > 180 AND comment_count = 0
```

### Using Cuts

Cuts referenced with `$name` in any WHERE position:

```
identify $trusted_authors
identify $trusted_authors AND $recent
hist age_days WHERE $active
plot age_days vs comment_count WHERE $trusted_authors AND $recent
bar author WHERE $stale
```

### Managing Cuts

```
cuts                    # list all defined cuts
cut $name expression    # define or update a cut
uncut $name             # remove a cut
```

### Composition

Cuts compose with standard boolean operators:

```
identify $trusted_authors AND $recent
identify $active OR $stale
identify NOT $stale
hist age_days WHERE $trusted_authors AND NOT $stale
```

## Use Case: Trusted Contributor Triage

The primary motivation is quick PR triage by known contributors:

```
# Define once per session (or load from file)
cut trusted author IN ('sdeleuze', 'markpollack', 'tzolov', 'cppwfs')
cut fresh created_at_dt > now-7d

# Quick triage
identify $trusted AND $fresh
identify $trusted AND age_days < 30
bar author WHERE $trusted

# Inverse — unknown contributors needing review
identify NOT $trusted AND $fresh
```

## Implementation Considerations

- Cuts are session-scoped (stored in CLI state)
- Could persist to `~/.prplot_cuts` for cross-session reuse
- Parser needs to resolve `$name` references before evaluation
- Recursive cut references (`$a` using `$b`) are out of scope initially
- Tab completion should include defined cut names after `$`
