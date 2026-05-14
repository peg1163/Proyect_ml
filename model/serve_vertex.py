from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from predictor import HousePricePredictor


class PredictionRequest(BaseModel):
    instances: list[dict[str, Any]]
    parameters: dict[str, Any] | None = None


app = FastAPI(title="House Price CatBoost Vertex AI Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
predictor = HousePricePredictor()


@app.on_event("startup")
def load_model() -> None:
    predictor.load()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/predict")
def predict(request: PredictionRequest) -> dict[str, list[float]]:
    try:
        predictions = predictor.predict(request.instances)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"predictions": predictions}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("AIP_HTTP_PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
