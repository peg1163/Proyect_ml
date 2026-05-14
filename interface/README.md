# Interfaz de prediccion

Esta carpeta contiene una interfaz simple en HTML, CSS y JavaScript para probar el modelo.

## Uso local

Primero levanta la API:

```bash
cd model
python serve_vertex.py
```

Luego abre:

```text
interface/index.html
```

El endpoint por defecto es:

```text
http://localhost:8080/predict
```

Si despliegas el modelo en otro servicio compatible con el formato `POST /predict`, cambia el campo `Endpoint` en la pantalla.

## Nota sobre Vertex AI

Un Vertex AI Endpoint usa autenticacion de Google Cloud. Para consumirlo desde un navegador normalmente necesitas un backend intermedio que firme/autentique la llamada, o usar esta interfaz apuntando a una API propia que haga de proxy hacia Vertex AI.
