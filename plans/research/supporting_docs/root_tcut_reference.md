# ROOT TCut Class Reference

> Source: https://root.cern/doc/master/classTCut.html

## Overview

TCut is a specialized string object used for TTree selections. It inherits from
TNamed and adds no data members — only operators for logical string concatenation.

## Constructors

```cpp
TCut()                                  // empty
TCut(const char *title)                 // e.g. TCut("x<1")
TCut(const char *name, const char *title)  // named: TCut("mycut", "x<1")
TCut(const TCut &cut)                   // copy
```

## Operators

| Operator | Meaning                | Example                          |
|----------|------------------------|----------------------------------|
| `=`      | Assignment             | `c1 = "x<1"`                     |
| `+=`     | Append with AND        | `c1 += "y>2"`                    |
| `+`      | Combine (OR-like)      | `c3 = c1 + c2`                   |
| `*`      | Combine (AND-like)     | `c3 = c1 * c2`                   |
| `&&`     | Logical AND            | `c3 = c1 && c2`                  |
| `||`     | Logical OR             | `c3 = c1 || c2`                  |
| `!`      | Logical NOT            | `c3 = !c1`                       |

## Usage Examples

```cpp
// Define named cuts
TCut cut1 = "x<1";
TCut cut2 = "y>2";
TCut cut3 = cut1 && cut2;   // → "(x<1)&&(y>2)"

// Use with TTree::Draw
MyTree->Draw("x", cut1);
MyTree->Draw("x", cut1 || "x>0");
MyTree->Draw("x", cut1 && cut2);

// Weighted expression with cut
MyTree->Draw("x", "(x+y)" * (cut1 && cut2));
```

## Key Design Points

- **Named**: Cuts have a name and title (inherited from TNamed)
- **Composable**: Combine cuts with logical operators to build complex selections
- **Reusable**: Define once, apply to many Draw calls
- **String-based**: Under the hood, just builds parenthesized string expressions
