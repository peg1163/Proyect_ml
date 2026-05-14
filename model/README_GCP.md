# Modelo final: grid_search_target_original

Este directorio contiene el codigo y los artefactos para entrenar y servir el modelo CatBoost con target original, usando los mejores parametros del grid search.

## Entrenar y guardar artefactos

Desde la raiz del proyecto:

```bash
python model/train_grid_search_target_original.py
```

Esto genera:

- `model/artifacts/catboost_grid_search_target_original.cbm`
- `model/artifacts/metrics_grid_search_target_original.json`
- `model/artifacts/predictions_grid_search_target_original.csv`
- `model/artifacts/feature_schema_grid_search_target_original.json`

## Probar prediccion local

```bash
python model/predictor.py
```

## Servir localmente como contenedor Vertex AI

Instala dependencias:

```bash
pip install -r model/requirements.txt
```

Levanta el servidor compatible con Vertex AI:

```bash
cd model
python serve_vertex.py
```

Prueba el endpoint local:

```bash
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d @model/sample_request.json
```

## Subida a GCP

Para subir los artefactos a Cloud Storage:

```bash
gcloud storage cp model/artifacts/* gs://TU_BUCKET/modelos/house-price-catboost/
```

O usando el script de Python:

```bash
pip install -r model/requirements.txt
python model/upload_artifacts_to_gcs.py --bucket TU_BUCKET --prefix modelos/house-price-catboost
```

Variables utiles para servir en un contenedor custom:

```bash
MODEL_ARTIFACTS_DIR=/ruta/local/a/artifacts
```

En Vertex AI, si los artefactos se descargan al contenedor, apunta `MODEL_ARTIFACTS_DIR` a esa carpeta. El predictor tambien revisa `AIP_STORAGE_URI` como fallback.

## Desplegar a Vertex AI Endpoint

Desde PowerShell, ejecuta:

```powershell
.\model\deploy_vertex_endpoint.ps1 `
  -ProjectId TU_PROJECT_ID `
  -Bucket TU_BUCKET `
  -Region us-central1
```

El script hace lo siguiente:

- entrena y regenera `model/artifacts`
- sube los artefactos a `gs://TU_BUCKET/modelos/house-price-catboost`
- crea un repositorio Docker en Artifact Registry si no existe
- construye la imagen con `Dockerfile.vertex`
- registra el modelo en Vertex AI Model Registry
- crea un Vertex AI Endpoint
- despliega el modelo al endpoint

Para pedir predicciones al endpoint:

```bash
gcloud ai endpoints predict ENDPOINT_ID \
  --region=us-central1 \
  --json-request=model/sample_request.json
```
