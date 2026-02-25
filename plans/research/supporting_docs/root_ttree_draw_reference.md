# ROOT TTree::Draw Reference

> Sources:
> - https://root.cern.ch/root/htmldoc/guides/users-guide/Trees.html
> - https://root.cern.ch/doc/master/classTTree.html
> - https://root.cern.ch/d/how/how-read-tree.html

## Method Signatures

```cpp
Long64_t Draw(const char *varexp, const char *selection,
              Option_t *option="", Long64_t nentries=kMaxEntries,
              Long64_t firstentry=0);

Long64_t Draw(const char *varexp, const TCut &selection,
              Option_t *option="", Long64_t nentries=kMaxEntries,
              Long64_t firstentry=0);
```

## Variable Expressions (varexp)

| Form           | Result              | Example                              |
|----------------|---------------------|--------------------------------------|
| `"x"`          | 1-D histogram       | `tree->Draw("age_days")`             |
| `"y:x"`        | 2-D scatter         | `tree->Draw("comments:age_days")`    |
| `"z:y:x"`      | 3-D scatter         | `tree->Draw("z:y:x")`               |
| `"sqrt(x)"`    | Computed expression | `tree->Draw("sqrt(fPx*fPx+fPy*fPy)")` |

## Selection Expressions

All C++ operators are valid in selections:

```cpp
// Simple comparisons
tree->Draw("x", "x>0");
tree->Draw("x", "y<100");

// Boolean logic
tree->Draw("x", "x<y && sqrt(z)>3.2");

// String equality
tree->Draw("Cost:Age", "Nation == \"FR\"");

// Weighted selection (non-boolean = weight value)
tree->Draw("x", "(x+y)*(sqrt(z)>3.2)");

// Conditional weights
tree->Draw("fBx", "fBx*fBx*(fBx>.4) + fBy*fBy*(fBy<=-.4)");
```

## Named Cuts with TCut

```cpp
TCut quality = "chi2 < 10";
TCut signal  = "mass > 80 && mass < 120";
TCut trigger = "trigger_bit == 1";

// Compose and reuse
tree->Draw("mass", quality && signal);
tree->Draw("pt",   quality && signal && trigger);
tree->Draw("eta",  quality && !signal);  // anti-signal region
```

## Directing Output to Named Histograms

```cpp
// Create/fill a named histogram
tree->Draw("x>>hname", "cuts");
TH1F *h = (TH1F*)gDirectory->Get("hname");

// Append to existing histogram
tree->Draw("x>>+hname", "more_cuts");

// Specify binning
tree->Draw("x>>hname(100,0,10)", "cuts");
```

## Draw Options

| Option  | Effect                                   |
|---------|------------------------------------------|
| `""`    | Default (histogram)                      |
| `"same"`| Superimpose on existing plot             |
| `"prof"` | Create TProfile instead of 2D histogram |
| `"profs"`| TProfile with error on spread           |
| `"goff"` | No graphics output (compute only)       |
| `"surf2"`| Surface plot for 2D                     |

## Entry Range Control

```cpp
// Process 1000 entries starting at entry 100
tree->Draw("Cost:Age", "", "", 1000, 100);
```

## Accessing Members and Methods

```cpp
tree->Draw("fNtrack");
tree->Draw("event.GetNtrack()");
tree->Draw("fH.fXaxis.fXmax");
tree->Draw("fH.GetXaxis().fXmax");
```

## Key Patterns for prplot

The one-liner pattern is central:
```
tree->Draw("what_to_plot", "which_entries_to_select");
```

This maps directly to prplot's:
```
hist what_to_plot WHERE which_entries_to_select
```

Named TCut objects map to prplot's planned "cut" feature — reusable aliases
for WHERE clauses that can be composed with logical operators.
