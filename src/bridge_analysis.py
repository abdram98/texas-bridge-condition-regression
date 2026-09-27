"""Reproducible preparation and regression for the Texas bridge sample."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_absolute_error,
    r2_score,
    root_mean_squared_error,
)
from sklearn.model_selection import KFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


PathLike = str | Path
Scope = Literal["all_complete", "under_80_nonhistoric"]
DATA_YEAR = 2019
ALL_COMPLETE: Scope = "all_complete"
FILTERED_SCOPE: Scope = "under_80_nonhistoric"

RATING_MAP = {
    "Failed": 0,
    "Failing": 1,
    "Critical": 2,
    "Serious": 3,
    "Poor": 4,
    "Fair": 5,
    "Satisfactory": 6,
    "Good": 7,
    "Very Good": 8,
    "Excellent": 9,
}

REQUIRED_COLUMNS = [
    "Structure_id",
    "Year",
    "AverageDaily",
    "Trucks_percent",
    "Historic",
    "Material",
    "Design",
    "Deck_rating",
    "Superstr_rating",
    "Substr_rating",
]
MODEL_FEATURES = [
    "Age",
    "AverageDaily",
    "Trucks_percent",
    "Material",
    "Design",
]
NUMERIC_FEATURES = ["Age", "AverageDaily", "Trucks_percent"]
CATEGORICAL_FEATURES = ["Material", "Design"]
RATING_COLUMNS = ["Deck_rating", "Superstr_rating", "Substr_rating"]


def load_bridge_data(path: PathLike) -> pd.DataFrame:
    """Load the prepared NBI bridge sample without changing the source file."""

    return pd.read_csv(path, dtype={"Structure_id": "string"})


def validate_bridge_data(data: pd.DataFrame) -> dict[str, object]:
    """Validate the expected schema and return concise source diagnostics."""

    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(data.columns))
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    unknown_ratings = sorted(
        {
            str(value)
            for column in RATING_COLUMNS
            for value in data[column].dropna().unique()
            if value not in RATING_MAP
        }
    )
    if unknown_ratings:
        raise ValueError(f"Unrecognised condition ratings: {unknown_ratings}")

    duplicate_ids = int(data["Structure_id"].duplicated().sum())
    if duplicate_ids:
        raise ValueError(f"Found {duplicate_ids} duplicate Structure_id values")

    return {
        "rows": int(len(data)),
        "columns": int(data.shape[1]),
        "duplicate_structure_ids": duplicate_ids,
        "missing_deck_ratings": int(data["Deck_rating"].isna().sum()),
        "missing_superstructure_ratings": int(
            data["Superstr_rating"].isna().sum()
        ),
        "missing_substructure_ratings": int(
            data["Substr_rating"].isna().sum()
        ),
        "minimum_year_built": int(data["Year"].min()),
        "maximum_year_built": int(data["Year"].max()),
    }


def _group_rare_categories(
    data: pd.DataFrame,
    column: str,
    threshold: float,
) -> pd.Series:
    proportions = data[column].value_counts(normalize=True)
    retained = set(proportions[proportions >= threshold].index)
    return data[column].where(data[column].isin(retained), "Other")


def prepare_bridge_data(
    data: pd.DataFrame,
    *,
    scope: Scope = FILTERED_SCOPE,
    data_year: int = DATA_YEAR,
    rare_category_threshold: float = 0.05,
) -> pd.DataFrame:
    """Create model features and the composite condition target.

    ``Year`` is treated as year built and age is aligned to the 2019 data
    vintage. The filtered scope excludes bridges aged 80 or older and bridges
    listed on the historic register. The complete-record scope retains them.
    """

    validate_bridge_data(data)
    if scope not in (ALL_COMPLETE, FILTERED_SCOPE):
        raise ValueError(f"Unsupported scope: {scope}")
    if not 0 <= rare_category_threshold <= 1:
        raise ValueError("rare_category_threshold must be between 0 and 1")

    prepared = data.dropna(subset=REQUIRED_COLUMNS).copy()
    prepared["Age"] = data_year - prepared["Year"]
    if (prepared["Age"] < 0).any():
        raise ValueError("Year built cannot be later than the data year")

    for column in RATING_COLUMNS:
        prepared[f"{column}_score"] = prepared[column].map(RATING_MAP).astype(int)
    prepared["Current_Condition"] = prepared[
        [f"{column}_score" for column in RATING_COLUMNS]
    ].sum(axis=1)

    if scope == FILTERED_SCOPE:
        prepared = prepared.loc[
            (prepared["Age"] < 80) & (prepared["Historic"] != "Register")
        ].copy()

    for column in CATEGORICAL_FEATURES:
        prepared[column] = _group_rare_categories(
            prepared,
            column,
            rare_category_threshold,
        )

    return prepared.reset_index(drop=True)


def build_regression_pipeline() -> Pipeline:
    """Create the one-hot-encoded ordinary least-squares pipeline."""

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(
                    drop="first",
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
                CATEGORICAL_FEATURES,
            )
        ],
        remainder="passthrough",
    )
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regression", LinearRegression()),
        ]
    )


@dataclass
class EvaluationResult:
    """Holdout and cross-validation results with fitted-model diagnostics."""

    scope: Scope
    observations: int
    holdout_r2: float
    holdout_rmse: float
    holdout_mae: float
    cv_r2_mean: float
    cv_r2_sd: float
    cv_rmse_mean: float
    cv_rmse_sd: float
    model: Pipeline
    holdout_actual: np.ndarray
    holdout_predicted: np.ndarray

    @property
    def holdout_residuals(self) -> np.ndarray:
        return self.holdout_actual - self.holdout_predicted

    def metrics(self) -> dict[str, object]:
        return {
            "scope": self.scope,
            "observations": self.observations,
            "holdout_r2": self.holdout_r2,
            "holdout_rmse": self.holdout_rmse,
            "holdout_mae": self.holdout_mae,
            "cv_r2_mean": self.cv_r2_mean,
            "cv_r2_sd": self.cv_r2_sd,
            "cv_rmse_mean": self.cv_rmse_mean,
            "cv_rmse_sd": self.cv_rmse_sd,
        }


def evaluate_regression(
    prepared: pd.DataFrame,
    *,
    scope: Scope,
    random_state: int = 42,
) -> EvaluationResult:
    """Evaluate the linear model with a holdout set and shuffled five-fold CV."""

    X = prepared[MODEL_FEATURES]
    y = prepared["Current_Condition"]
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=random_state,
    )

    holdout_model = build_regression_pipeline()
    holdout_model.fit(X_train, y_train)
    predictions = holdout_model.predict(X_test)

    cv = KFold(n_splits=5, shuffle=True, random_state=random_state)
    scores = cross_validate(
        build_regression_pipeline(),
        X,
        y,
        cv=cv,
        scoring={"r2": "r2", "rmse": "neg_root_mean_squared_error"},
    )

    final_model = build_regression_pipeline()
    final_model.fit(X, y)

    return EvaluationResult(
        scope=scope,
        observations=len(prepared),
        holdout_r2=float(r2_score(y_test, predictions)),
        holdout_rmse=float(root_mean_squared_error(y_test, predictions)),
        holdout_mae=float(mean_absolute_error(y_test, predictions)),
        cv_r2_mean=float(scores["test_r2"].mean()),
        cv_r2_sd=float(scores["test_r2"].std(ddof=1)),
        cv_rmse_mean=float((-scores["test_rmse"]).mean()),
        cv_rmse_sd=float((-scores["test_rmse"]).std(ddof=1)),
        model=final_model,
        holdout_actual=y_test.to_numpy(),
        holdout_predicted=np.asarray(predictions),
    )


def coefficient_table(result: EvaluationResult) -> pd.DataFrame:
    """Return labelled coefficients from the final model fitted to its full scope."""

    preprocessor = result.model.named_steps["preprocessor"]
    regression = result.model.named_steps["regression"]
    labels = preprocessor.get_feature_names_out()
    readable = [
        label.replace("categorical__", "")
        .replace("remainder__", "")
        .replace("Material_", "Material: ")
        .replace("Design_", "Design: ")
        for label in labels
    ]
    return pd.DataFrame(
        {
            "Predictor": readable,
            "Coefficient": regression.coef_,
        }
    ).sort_values("Coefficient")


def continuous_range_effects(
    prepared: pd.DataFrame,
    result: EvaluationResult,
) -> pd.DataFrame:
    """Express continuous coefficients over each feature's 10th-90th range."""

    coefficients = coefficient_table(result).set_index("Predictor")["Coefficient"]
    target_range = (
        prepared["Current_Condition"].quantile(0.9)
        - prepared["Current_Condition"].quantile(0.1)
    )
    rows = []
    for feature in NUMERIC_FEATURES:
        feature_range = prepared[feature].quantile(0.9) - prepared[feature].quantile(0.1)
        point_effect = coefficients[feature] * feature_range
        rows.append(
            {
                "Predictor": feature,
                "10th-90th range": feature_range,
                "Condition-point effect": point_effect,
                "Percent of target range": 100 * point_effect / target_range,
            }
        )
    return pd.DataFrame(rows)


def sensitivity_analysis(
    data: pd.DataFrame,
    *,
    random_state: int = 42,
) -> tuple[pd.DataFrame, dict[Scope, EvaluationResult]]:
    """Compare model performance with and without the age/historic exclusion."""

    results: dict[Scope, EvaluationResult] = {}
    for scope in (ALL_COMPLETE, FILTERED_SCOPE):
        prepared = prepare_bridge_data(data, scope=scope)
        results[scope] = evaluate_regression(
            prepared,
            scope=scope,
            random_state=random_state,
        )
    table = pd.DataFrame([result.metrics() for result in results.values()])
    return table, results
