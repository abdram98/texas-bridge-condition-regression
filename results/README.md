# Results

## Population and preparation

| Stage or scope | Records |
|---|---:|
| Source sample | 34,293 |
| Complete condition and predictor records | 34,286 |
| Under 80 and not historically registered | 31,905 |

Age is aligned with the 2019 data vintage. The restricted scope removes 2,381
complete records based on age or historic-register status.

## Out-of-sample performance

| Scope | Holdout R² | Holdout RMSE | Holdout MAE | Mean CV R² | CV R² SD | Mean CV RMSE | CV RMSE SD |
|---|---:|---:|---:|---:|---:|---:|---:|
| All complete records | 0.4548 | 1.4694 | 1.0953 | 0.4505 | 0.0146 | 1.4858 | 0.0285 |
| Under 80 and not historically registered | 0.4556 | 1.4336 | 1.0751 | 0.4552 | 0.0155 | 1.4324 | 0.0359 |

The holdout set contains 20% of each analysis scope and uses random state 42.
Cross-validation uses five shuffled folds with the same fixed random state.

## Filtered-scope coefficients

The reference categories are concrete material and beam design.

| Predictor | Coefficient |
|---|---:|
| Material: Other | -2.8408 |
| Material: Steel | -1.3812 |
| Age, per year | -0.0556 |
| Average daily traffic, per vehicle | -0.0000002 |
| Truck share, per percentage point | +0.0055 |
| Design: Slab | +0.0467 |
| Design: Other | +0.0720 |

Because the numeric predictors have different units, their raw coefficients
should not be ranked directly. Across each variable's 10th-to-90th percentile
range:

| Predictor | Observed range | Fitted condition-point difference |
|---|---:|---:|
| Age | 53 years | -2.948 |
| Average daily traffic | 30,700 vehicles | -0.007 |
| Truck share | 23 percentage points | +0.126 |

## Sensitivity conclusion

Retaining very old and historically registered bridges changes mean
cross-validated R² by less than 0.005. Age and material coefficients remain the
largest fitted associations, and traffic and design effects remain small. The
similarity supports the robustness of the descriptive conclusion, but it does
not establish causality.
