# Texas Bridge Condition Regression

An interpretable regression analysis of a prepared sample from the 2019 US
National Bridge Inventory. The project examines how bridge age, traffic,
truck share, material and structural design are associated with a composite
condition score.

## Project highlights

- Validated **34,293 Texas bridge records** and 25 source variables.
- Constructed a 0-27 condition score from deck, superstructure and
  substructure ratings.
- Aligned bridge age with the **2019 data vintage** rather than the analysis
  date.
- Compared a complete-record model with a restricted model excluding bridges
  aged 80 or older and historically registered bridges.
- Evaluated ordinary least squares using a fixed 20% holdout set and shuffled
  five-fold cross-validation.
- Used an explicit preprocessing pipeline for categorical encoding and
  retained named regression coefficients for interpretation.

## Questions

1. Which proposed predictors have the strongest association with bridge
   condition?
2. How accurately does the linear model predict the composite condition score?
3. Do the conclusions change when very old and historically registered bridges
   are retained?

## Model performance

| Scope | Records | Holdout R² | Holdout RMSE | Mean CV R² | Mean CV RMSE |
|---|---:|---:|---:|---:|---:|
| All complete records | 34,286 | 0.455 | 1.469 | 0.451 | 1.486 |
| Under 80 and not historically registered | 31,905 | 0.456 | 1.434 | 0.455 | 1.432 |

The filtered model explains approximately **45.5%** of unseen variation in the
composite condition score. Its typical cross-validated prediction error is
approximately **1.43 points** on the 0-27 scale. The similarity between the two
scopes indicates that the main results are not driven solely by the exclusion
of older and historically registered bridges.

## Main findings

In the filtered model, each additional year of age is associated with a
**0.0556-point reduction** in condition after controlling for the other model
variables. Across the observed 10th-to-90th percentile age range of 53 years,
this corresponds to approximately **2.95 condition points**, or 59% of the
target's comparable percentile range.

Relative to concrete bridges, the fitted differences are approximately:

- **-1.38 points for steel**; and
- **-2.84 points for the heterogeneous “Other” material group**.

Average daily traffic has a near-zero range effect, while the estimated effect
of truck share is small. Design coefficients are also close to zero after
controlling for the other predictors. These coefficients describe conditional
associations in this sample and should not be interpreted as causal effects of
material or age.

## Method

1. Validated the source schema, unique structure identifiers, rating labels and
   missing values.
2. Removed seven records missing a deck or superstructure rating.
3. Calculated age as `2019 - Year`, where `Year` represents year built.
4. Converted the three component ratings from Failed=0 through Excellent=9 and
   summed them into the condition target.
5. Combined categories representing less than 5% of the analysis scope into
   `Other`.
6. One-hot encoded material and design within a scikit-learn pipeline.
7. Evaluated the model with a holdout set and shuffled five-fold
   cross-validation before fitting the final coefficient model on each scope.
8. Compared residuals, coefficients and model performance across both scopes.

## Data source

The included `tx19_bridges_sample.csv` is a simplified sample derived from the
Federal Highway Administration's 2019 National Bridge Inventory. The official
2019 download page reports 54,432 Texas highway bridges; this prepared file
contains 34,293 records and is not the complete state inventory.

The underlying NBI data are published as US Government public-domain data.
Source and reuse details are documented in
[`data/ATTRIBUTION.md`](data/ATTRIBUTION.md).

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
jupyter lab notebooks/texas_bridge_condition_regression.ipynb
```

## Repository structure

```text
texas-bridge-condition-regression/
├── README.md
├── data/
│   ├── ATTRIBUTION.md
│   ├── README.md
│   └── raw/tx19_bridges_sample.csv
├── notebooks/
│   └── texas_bridge_condition_regression.ipynb
├── results/
│   └── README.md
├── src/
│   ├── __init__.py
│   └── bridge_analysis.py
├── tests/
│   └── test_bridge_analysis.py
├── .gitignore
└── requirements.txt
```

## Interpretation boundaries

- The prepared data are a simplified subset, not the full 2019 Texas NBI.
- The composite target adds three ordinal condition ratings and therefore
  assumes equal spacing and equal component importance.
- The dataset is cross-sectional. Regression coefficients cannot establish
  that a predictor caused the observed condition difference.
- The model omits inspection history, reconstruction year, climate exposure,
  maintenance activity, loading history and other potentially relevant
  variables.
- The `Other` material category combines several uncommon materials and should
  not be treated as one engineering class.
- Residuals retain a negative skew, indicating that linear-model errors are not
  perfectly symmetric.
