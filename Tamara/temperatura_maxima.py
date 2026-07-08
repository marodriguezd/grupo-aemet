import os
import pickle
import numpy as np
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Request, Path
import pandas as pd
from typing import List
import psycopg

router_temp_max = APIRouter(prefix="/modelos_max", tags=["modelos_max"])
cache_modelos_max = {}

user = "postgres"
password = "postgres"
host = "localhost"
port = "5432"
database = "aemet"

dsn = f"postgresql://{user}:{password}@{host}:{port}/{database}"

print(dsn)

# Ruta absoluta base corregida
BASE_DIR = os.path.dirname(os.path.abspath(_file_))

class PredictionInput(BaseModel):
    features: List[float] = Field(..., description="Lista de características numéricas para el modelo")

def obtener_modelo_max(idema: str):
    if idema in cache_modelos_max:
        return cache_modelos_max[idema]

    # CORRECCIÓN: Uso de ruta absoluta
    ruta_archivo = os.path.join(BASE_DIR, "modelos_max", f"modelo_{idema}_max.pkl")

    if not os.path.exists(ruta_archivo):
        return None

    try:
        with open(file=ruta_archivo, mode="rb") as file:
            modelo = pickle.load(file)
        cache_modelos_max[idema] = modelo
        return modelo
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al cargar el archivo de modelo: {str(e)}"
        )
@router_temp_max.get(
    path="/{idema}/predict",
    summary="Predicción de temperatura máxima",
    description="Genera la predicción de temperatura máxima usando el modelo específico de una estación IDEMA."
)
def prediccion_temp_max_endpoint(
    idema: str = Path(..., description="Código identificador de la estación (IDEMA)"),
    # input_data: PredictionInput = None
):

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cursor:

            cursor.execute(query = f"SELECT tmax FROM datos_climaticos WHERE id = '{idema}' ORDER BY fecha DESC LIMIT 1;")

            input_data = cursor.fetchall()[0][0]

    modelo = obtener_modelo_max(idema)

    try:
    # Convertir a matriz 2D para la predicción
        if modelo is None:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró un modelo para la estación con IDEMA: {idema}"
            )

        else:
            X = np.array([input_data.features])
            prediccion_numpy = modelo.predict(X)
            prediccion = prediccion_numpy.tolist()

        return {
            "status": "success",
            "idema": idema,
            "mensaje": "Predicción de temperatura máxima obtenida correctamente",
            "prediccion": prediccion
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno al ejecutar la predicción del modelo: {str(e)}"
        )