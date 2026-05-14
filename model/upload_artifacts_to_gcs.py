from __future__ import annotations

import argparse
from pathlib import Path

from google.cloud import storage


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACTS_DIR = ROOT_DIR / "model" / "artifacts"


def upload_directory(bucket_name: str, source_dir: Path, prefix: str) -> None:
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    prefix = prefix.strip("/")
    for path in source_dir.rglob("*"):
        if not path.is_file():
            continue

        relative_path = path.relative_to(source_dir).as_posix()
        blob_name = f"{prefix}/{relative_path}" if prefix else relative_path
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(path)
        print(f"gs://{bucket_name}/{blob_name}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sube los artefactos del modelo CatBoost a Google Cloud Storage."
    )
    parser.add_argument("--bucket", required=True, help="Nombre del bucket sin gs://")
    parser.add_argument(
        "--prefix",
        default="modelos/house-price-catboost",
        help="Carpeta destino dentro del bucket",
    )
    parser.add_argument(
        "--source-dir",
        default=str(DEFAULT_ARTIFACTS_DIR),
        help="Directorio local con artefactos del modelo",
    )
    args = parser.parse_args()

    upload_directory(args.bucket, Path(args.source_dir), args.prefix)


if __name__ == "__main__":
    main()
