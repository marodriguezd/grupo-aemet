# -*- coding: utf-8 -*-
"""
API backend con FastAPI para predicciones y consulta histórica.
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import psycopg
from datetime import date
import os
import pickle
import numpy as np

app = FastAPI(title="AEMET", description="API de AEMET", version="1.0")

# ---- Credenciales de BD ----
HOST = "database-dai07rt-proyecto-aemet-2026.cr828ecqk1a6.eu-central-1.rds.amazonaws.com"
PORT = "5432"
DBNAME = "postgres"
USER = "aemet2026"
PASSWORD = "mondongo-dai07rt-aemet-2026"
DSN = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cache_modelos_max = {}
cache_modelos_min = {}

def obtener_modelo(idema: str, tipo: str):
    cache = cache_modelos_max if tipo == "max" else cache_modelos_min
    if idema in cache:
        return cache[idema]
    
    ruta_archivo = os.path.join(BASE_DIR, f"modelos_{tipo}", f"modelo_{idema}_{tipo}.pkl")
    
    if not os.path.exists(ruta_archivo):
        return None
    
    try:
        with open(file=ruta_archivo, mode="rb") as file:
            modelo = pickle.load(file)
        cache[idema] = modelo
        return modelo
    except Exception as e:
        print(f"Error al cargar el archivo de modelo {tipo}: {str(e)}")
        return None

class InputFeatures(BaseModel):
    features: list

@app.get("/")
def bienvenida():
    return {"mensaje": "Bienvenido a la API de AEMET. Ve a /docs para más info."}

@app.post("/modelos_max/{idema}/predict")
def prediccion_temp_max(idema: str, input_data: InputFeatures):
    """Devuelve predicción de temp máxima o simulación si no hay modelo."""
    print(f"Calculando temp máxima para {idema}...")
    modelo = obtener_modelo(idema, "max")
    
    if modelo is None:
        valor_simulado = input_data.features[0] * 1.5 + 5.0
        prediccion = [[valor_simulado]]
        mensaje = "Predicción simulada (modelo no encontrado)"
    else:
        X = np.array([input_data.features])
        prediccion = modelo.predict(X).tolist()
        mensaje = "Predicción real calculada correctamente"
        
    return {
        "status": "success",
        "idema": idema,
        "mensaje": mensaje,
        "prediccion": prediccion
    }

@app.post("/modelos_min/{idema}/predict")
def prediccion_temp_min(idema: str, input_data: InputFeatures):
    """Devuelve predicción de temp mínima o simulación si no hay modelo."""
    print(f"Calculando temp mínima para {idema}...")
    modelo = obtener_modelo(idema, "min")
    
    if modelo is None:
        valor_simulado = input_data.features[0] * 0.8 - 2.0
        prediccion = [[valor_simulado]]
        mensaje = "Predicción simulada (modelo no encontrado)"
    else:
        X = np.array([input_data.features])
        prediccion = modelo.predict(X).tolist()
        mensaje = "Predicción real calculada correctamente"
        
    return {
        "status": "success",
        "idema": idema,
        "mensaje": mensaje,
        "prediccion": prediccion
    }

@app.get("/historico/obtener_historico")
def obtener_historico(
    idema: str = Query(..., alias="id"),
    fecha_inicio: date = Query(...),
    fecha_fin: date = Query(...)
):
    """Consulta el histórico directamente a la base de datos."""
    if fecha_inicio > fecha_fin:
        raise HTTPException(status_code=400, detail="Fechas incorrectas")

    print(f"Consultando histórico de {idema}...")
    try:
        with psycopg.connect(DSN) as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT fecha, tmax, tmed, tmin 
                    FROM datos_climaticos 
                    WHERE indicativo = %s AND fecha >= %s AND fecha <= %s
                    ORDER BY fecha;
                """
                cur.execute(query, (idema, fecha_inicio, fecha_fin))
                filas = cur.fetchall()

        registros = []
        for fila in filas:
            registros.append({
                "fecha": str(fila[0]),
                "tmax": float(fila[1]) if fila[1] else None,
                "tmed": float(fila[2]) if fila[2] else None,
                "tmin": float(fila[3]) if fila[3] else None
            })

        return {"registros": registros}
    except Exception as e:
        print(f"Error en BD: {e}")
        raise HTTPException(status_code=500, detail="Error al conectar a la BD")


