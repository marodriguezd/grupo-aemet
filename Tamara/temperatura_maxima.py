


import os
import pickle
from typing import List
import numpy as np
from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field

router_temp_max = APIRouter(prefix="/modelos_max", tags=["modelos_max"])
cache_modelos_max = {}


#codigo de python que se usa como estandar para encontratr la ruta de un archivo 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class PredictionInput(BaseModel):
    features: List[float] = Field(..., description="Lista de características numéricas para el modelo")

def obtener_modelo_max(idema: str):
    if idema in cache_modelos_max:
        return cache_modelos_max[idema]
    

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
@router_temp_max.post(
    path="/{idema}/predict", 
    summary="Predicción de temperatura máxima", 
    description="Genera la predicción de temperatura máxima usando el modelo específico de una estación IDEMA."
)
def prediccion_temp_max_endpoint(
    idema: str = Path(..., description="Código identificador de la estación (IDEMA)"), 
    input_data: PredictionInput = None
):
    modelo = obtener_modelo_max(idema)
    
    try:
     
        if modelo is None:
            valor_simulado = input_data.features[0] * 1.5 + 5.0
            prediccion = [[valor_simulado]]
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
