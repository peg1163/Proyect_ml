from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACTS_DIR = ROOT_DIR / "model" / "artifacts"
DEFAULT_MODEL_FILE = "catboost_grid_search_target_original.cbm"
DEFAULT_SCHEMA_FILE = "feature_schema_grid_search_target_original.json"


def _download_gcs_directory(gcs_uri: str, destination: Path) -> Path:
    from google.cloud import storage

    if not gcs_uri.startswith("gs://"):
        raise ValueError(f"URI de GCS invalida: {gcs_uri}")

    bucket_name, _, prefix = gcs_uri[5:].partition("/")
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    destination.mkdir(parents=True, exist_ok=True)
    for blob in client.list_blobs(bucket, prefix=prefix):
        if blob.name.endswith("/"):
            continue

        relative_name = blob.name[len(prefix) :].lstrip("/") if prefix else blob.name
        local_path = destination / relative_name
        local_path.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(local_path)

    return destination


def _resolve_artifacts_dir(artifacts_dir: str | Path | None = None) -> Path:
    configured_dir = (
        str(artifacts_dir)
        if artifacts_dir is not None
        else os.getenv("MODEL_ARTIFACTS_DIR") or os.getenv("AIP_STORAGE_URI")
    )

    if not configured_dir:
        return DEFAULT_ARTIFACTS_DIR

    if configured_dir.startswith("gs://"):
        return _download_gcs_directory(configured_dir, Path("/tmp/model_artifacts"))

    return Path(configured_dir)


class HousePricePredictor:
    """Small prediction wrapper ready to reuse from scripts or a GCP container."""

    def __init__(self, artifacts_dir: str | Path | None = None) -> None:
        self.artifacts_dir = _resolve_artifacts_dir(artifacts_dir)
        self.model = CatBoostRegressor()
        self.schema: dict[str, Any] = {}

    def load(self) -> None:
        schema_path = self.artifacts_dir / DEFAULT_SCHEMA_FILE
        model_path = self.artifacts_dir / DEFAULT_MODEL_FILE

        self.schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.model.load_model(model_path)

    def preprocess(self, records: list[dict[str, Any]] | pd.DataFrame) -> pd.DataFrame:
        df = pd.DataFrame(records).copy()
        anio_actual = pd.Timestamp.today().year

        if "yr_built" in df.columns:
            df["data_modelod_fabricacion"] = anio_actual - df["yr_built"]
        if "yr_renovated" in df.columns:
            df["data_modelod_renovacion"] = np.where(
                df["yr_renovated"] > 0,
                anio_actual - df["yr_renovated"],
                0,
            )
            df["tiene_renov"] = np.where(
                df["data_modelod_renovacion"] == 0,
                "No",
                "Si",
            )

        drop_cols = [
            "id",
            "date",
            "yr_built",
            "yr_renovated",
            "sqft_living15",
            "sqft_lot15",
            "waterfront",
            "data_modelod_fabricacion",
            "sqft_basement",
            "bathrooms",
            "condition",
            "floors",
            "bedrooms",
            "tiene_renov",
            "data_modelod_renovacion",
            "price",
        ]
        df = df.drop(columns=drop_cols, errors="ignore")

        feature_columns = self.schema["feature_columns"]
        missing_columns = [col for col in feature_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Faltan columnas requeridas: {missing_columns}")

        df = df[feature_columns]

        for col in self.schema["categorical_features"]:
            df[col] = df[col].astype(str)

        return df

    def predict(self, records: list[dict[str, Any]] | pd.DataFrame) -> list[float]:
        features = self.preprocess(records)
        return self.model.predict(features).astype(float).tolist()


_PREDICTOR: HousePricePredictor | None = None


def predict(instances: list[dict[str, Any]]) -> dict[str, list[float]]:
    """Prediction entry point compatible with simple custom serving adapters."""
    global _PREDICTOR
    if _PREDICTOR is None:
        _PREDICTOR = HousePricePredictor()
        _PREDICTOR.load()

    return {"predictions": _PREDICTOR.predict(instances)}


if __name__ == "__main__":
    sample_path = ROOT_DIR / "data" / "raw" / "kc_house_data.csv"
    sample = pd.read_csv(sample_path).head(5)

    predictor = HousePricePredictor()
    predictor.load()
    print(predictor.predict(sample))
