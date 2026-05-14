from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT_DIR / "data" / "raw" / "kc_house_data.csv"
ARTIFACTS_DIR = ROOT_DIR / "model" / "artifacts"

TARGET = "price"
RANDOM_STATE = 42
TEST_SIZE = 0.2

MODEL_FILENAME = "catboost_grid_search_target_original.cbm"
METRICS_FILENAME = "metrics_grid_search_target_original.json"
PREDICTIONS_FILENAME = "predictions_grid_search_target_original.csv"
SCHEMA_FILENAME = "feature_schema_grid_search_target_original.json"

COLUMNAS_BASE_A_ELIMINAR = [
    "id",
    "date",
    "yr_built",
    "yr_renovated",
    "sqft_living15",
    "sqft_lot15",
]

COLUMNAS_ELIMINAR = [
    "waterfront",
    "data_modelod_fabricacion",
    "sqft_basement",
    "bathrooms",
    "condition",
    "floors",
    "bedrooms",
    "tiene_renov",
    "data_modelod_renovacion",
]

COLUMNAS_CATEGORICAS = ["view", "grade", "zipcode"]

PARAMS_GRID_SEARCH = {
    "iterations": 100,
    "learning_rate": 0.05,
    "depth": 6,
    "l2_leaf_reg": 3,
    "loss_function": "RMSE",
    "eval_metric": "RMSE",
    "random_seed": RANDOM_STATE,
    "verbose": 0,
    "allow_writing_files": False,
}


def preparar_datos(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    data_modelo = df.copy()
    anio_actual = pd.Timestamp.today().year

    data_modelo["data_modelod_fabricacion"] = anio_actual - data_modelo["yr_built"]
    data_modelo["data_modelod_renovacion"] = np.where(
        data_modelo["yr_renovated"] > 0,
        anio_actual - data_modelo["yr_renovated"],
        0,
    )
    data_modelo["tiene_renov"] = np.where(
        data_modelo["data_modelod_renovacion"] == 0,
        "No",
        "Si",
    )

    data_modelo = data_modelo.drop(columns=COLUMNAS_BASE_A_ELIMINAR, errors="ignore")
    data_modelo = data_modelo.drop(columns=COLUMNAS_ELIMINAR, errors="ignore")

    cat_features = [col for col in COLUMNAS_CATEGORICAS if col in data_modelo.columns]
    for col in cat_features:
        data_modelo[col] = data_modelo[col].astype(str)

    X = data_modelo.drop(columns=[TARGET])
    y = data_modelo[TARGET].copy()

    return X, y, cat_features


def obtener_metricas(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "R2": float(r2_score(y_true, y_pred)),
    }


def guardar_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_PATH)
    X, y, cat_features = preparar_datos(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )

    model = CatBoostRegressor(**PARAMS_GRID_SEARCH)
    model.fit(
        X_train,
        y_train,
        cat_features=cat_features,
        eval_set=(X_test, y_test),
        use_best_model=True,
    )

    y_pred = model.predict(X_test)
    metrics = obtener_metricas(y_test, y_pred)

    model_path = ARTIFACTS_DIR / MODEL_FILENAME
    metrics_path = ARTIFACTS_DIR / METRICS_FILENAME
    predictions_path = ARTIFACTS_DIR / PREDICTIONS_FILENAME
    schema_path = ARTIFACTS_DIR / SCHEMA_FILENAME

    model.save_model(model_path)

    predictions = pd.DataFrame(
        {
            "y_real": y_test,
            "y_pred": y_pred,
            "error": y_test - y_pred,
            "abs_error": np.abs(y_test - y_pred),
        },
        index=y_test.index,
    )
    predictions.index.name = "row_id"
    predictions.to_csv(predictions_path)

    schema = {
        "target": TARGET,
        "feature_columns": X.columns.tolist(),
        "categorical_features": cat_features,
        "params": PARAMS_GRID_SEARCH,
        "test_size": TEST_SIZE,
        "random_state": RANDOM_STATE,
        "target_transform": "none",
        "model_file": MODEL_FILENAME,
    }

    guardar_json(
        metrics_path,
        {
            "model_name": "grid_search_target_original",
            "metrics": metrics,
            "artifacts": {
                "model": model_path.relative_to(ROOT_DIR).as_posix(),
                "predictions": predictions_path.relative_to(ROOT_DIR).as_posix(),
                "schema": schema_path.relative_to(ROOT_DIR).as_posix(),
            },
        },
    )
    guardar_json(schema_path, schema)

    print("Modelo guardado en:", model_path)
    print("Metricas guardadas en:", metrics_path)
    print("Predicciones guardadas en:", predictions_path)
    print("Schema guardado en:", schema_path)
    print(pd.DataFrame([metrics]).to_string(index=False))


if __name__ == "__main__":
    main()
