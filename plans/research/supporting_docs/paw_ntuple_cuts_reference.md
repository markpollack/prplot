# PAW Ntuple Cuts Reference

> Sources:
> - https://paw.web.cern.ch/paw/tutorial/
> - https://paw.web.cern.ch/paw/tutorial/tut038.html (Simple selection criteria)
> - https://paw.web.cern.ch/paw/tutorial/tut041.html (Ntuple cuts)
> - https://paw.web.cern.ch/paw/tutorial/tut040.html (Masks and loops)

## Inline Selection Criteria

Selection criteria are passed as the second parameter to NT/PLOT and NT/SCAN:

```
NT/PLOT //LUN3/11.SERVICE NATION='FR' OPTION=S IDH=200
NT/PLOT //LUN3/11.Service division='EP'.and.nation='FR' OPTION=S IDH=200
NT/SCAN //LUN3/11 nation='FR'.and.division='EP'
```

### Operators

| Operator       | Meaning     |
|----------------|-------------|
| `.AND.`        | Logical AND |
| `.OR.`         | Logical OR  |
| `.EQ.`         | Equal       |
| `.NE.`         | Not equal   |
| `.GT.`         | Greater than|
| `.LT.`         | Less than   |
| `.GE.`         | >= |
| `.LE.`         | <= |

## Named Cuts ($-notation)

Cuts are defined with the `CUT` command using `$nn` identifiers:

```
CUT $1 MOD(INT(FLAG),2).EQ.0
CUT $2 MOD(INT(FLAG),4)>1
```

### Applying Named Cuts

Named cuts are passed by reference in NT/PLOT:

```
ntuple/plot 10.division $1 option=S idh=20
ntuple/plot 10.division $2 option=S idh=20
ntuple/plot 10.division $1.and.$2 option=S idh=20
```

### Cut Management (NTUPLE/CUTS)

The `NTUPLE/CUTS` command manages named cuts:
- Define, list, write to file, read from file

## Masks (Pre-computed Cuts)

Masks store cut results as bitmasks for fast reuse. Useful when selection is
expensive and applied repeatedly.

### Create and Fill Masks

```
MASK/FILE STMASK n

NT/LOOP 10 STEP=15>>STMASK(1)
NT/LOOP 10 grade>4.and.step=13>>STMASK(2)
NT/LOOP 10 (grade=13.and.step=10).or.(grade=14.and.step=7)>>STMASK(3)
```

### Use Masks in Plots

```
NT/PLOT 10.GRADE STMASK(1).OR.STMASK(2).OR.STMASK(3)>>STMASK(4) OPTION=S IDH=20
```

### Performance

Pre-computed masks are faster than inline expressions:
```
NTUPLE/PLOT 10.GRADE STMASK(3)
  vs.
NTUPLE/PLOT 10.GRADE (grade=13.AND.step=10).OR.(grade=14.AND.step=7)
```

## Graphical Cuts (NTUPLE/GCUT)

Interactive mouse-drawn selection regions on 2D plots. Limited to original
ntuple variables (not computed expressions).

## Key Patterns for prplot

| PAW Concept        | prplot Equivalent                                |
|--------------------|--------------------------------------------------|
| Inline selection   | `WHERE state = 'open' AND age_days > 90`         |
| Named cut `$1`     | Planned: `cut trusted_authors author IN (...)`    |
| Cut composition    | Planned: `$trusted_authors AND age_days < 30`     |
| Masks              | Not needed (dataset fits in memory)               |
| Graphical cuts     | Click-to-identify on scatter plots                |
