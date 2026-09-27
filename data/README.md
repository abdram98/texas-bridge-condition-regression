# Data

## Included file

`raw/tx19_bridges_sample.csv` contains 34,293 bridge records and 25 columns.
The file is a prepared subset derived from the 2019 National Bridge Inventory.

The source file is preserved unchanged. Validation found:

- 34,293 unique structure identifiers;
- no duplicated `Structure_id` values;
- five missing deck ratings;
- two missing superstructure ratings;
- no missing substructure ratings; and
- construction years ranging from 1900 to 2019.

Seven incomplete records are removed during analysis. The source CSV itself is
not modified.

## Model fields

| Field | Use |
|---|---|
| `Year` | Year built; used to calculate age relative to 2019 |
| `AverageDaily` | Average daily traffic |
| `Trucks_percent` | Truck share of traffic |
| `Historic` | Used for the restricted-scope sensitivity analysis |
| `Material` | Primary construction-material category |
| `Design` | Structural design category |
| `Deck_rating` | Component condition rating |
| `Superstr_rating` | Component condition rating |
| `Substr_rating` | Component condition rating |

The composite target is created during analysis and is not written back to the
raw file.

## Integrity check

The expected SHA-256 checksum is:

```text
93040d8b0ada780c5ca8bbd884451949f6562dd87e5d6e586d8274a636748206
```

See `ATTRIBUTION.md` for the official source and public-domain status.
