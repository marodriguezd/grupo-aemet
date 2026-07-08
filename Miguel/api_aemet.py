# -*- coding: utf-8 -*-
"""
API backend con FastAPI para predicciones y consulta histórica.
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import psycopg
from datetime import date
import pickle
import os
import pandas as pd
import xgboost as xgb

app = FastAPI(title="AEMET", description="API de AEMET", version="1.0")

# ---- Credenciales de BD ----
HOST = "database-dai07rt-proyecto-aemet-2026.cr828ecqk1a6.eu-central-1.rds.amazonaws.com"
PORT = "5432"
DBNAME = "postgres"
USER = "aemet2026"
PASSWORD = "mondongo-dai07rt-aemet-2026"
DSN = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"

class InputFeatures(BaseModel):
    features: list

@app.get("/")
def bienvenida():
    return {"mensaje": "Bienvenido a la API de AEMET. Ve a /docs para más info."}

@app.get("/estaciones/lista")
def lista_estaciones():
    """Devuelve la lista completa de estaciones disponibles."""
    try:
        with psycopg.connect(DSN) as conn:
            with conn.cursor() as cur:
                query = "SELECT DISTINCT indicativo, nombre, provincia FROM datos_climaticos WHERE indicativo IS NOT NULL ORDER BY nombre;"
                cur.execute(query)
                filas = cur.fetchall()
        return {"estaciones": [{"idema": f[0], "nombre": f[1], "provincia": f[2]} for f in filas]}
    except Exception as e:
        print(f"Error BD estaciones: {e}")
        raise HTTPException(status_code=500, detail="Error al cargar las estaciones")

@app.post("/modelos_max/{idema}/predict")
def prediccion_temp_max(idema: str, input_data: InputFeatures):
    """Predicción real de temperatura máxima con XGBoost."""
    idema_limpio = idema.strip().replace("/", "_").replace("\\", "_")
    ruta_modelo = f"modelos_max/modelo_{idema_limpio}_max.pkl"
    if not os.path.exists(ruta_modelo):
        raise HTTPException(status_code=404, detail="Modelo no entrenado para esta estación")

    with open(ruta_modelo, "rb") as f:
        modelo = pickle.load(f)

    df_in = pd.DataFrame([{"tmed": input_data.features[0]}])
    valor_pred = float(modelo.predict(df_in)[0])

    return {
        "status": "success",
        "idema": idema,
        "mensaje": "Predicción real (XGBoost)",
        "prediccion": [[valor_pred]]
    }

@app.post("/modelos_min/{idema}/predict")
def prediccion_temp_min(idema: str, input_data: InputFeatures):
    """Predicción real de temperatura mínima con XGBoost."""
    idema_limpio = idema.strip().replace("/", "_").replace("\\", "_")
    ruta_modelo = f"modelos_min/modelo_{idema_limpio}_min.pkl"
    if not os.path.exists(ruta_modelo):
        raise HTTPException(status_code=404, detail="Modelo no entrenado para esta estación")

    with open(ruta_modelo, "rb") as f:
        modelo = pickle.load(f)

    df_in = pd.DataFrame([{"tmed": input_data.features[0]}])
    valor_pred = float(modelo.predict(df_in)[0])

    return {
        "status": "success",
        "idema": idema,
        "mensaje": "Predicción real (XGBoost)",
        "prediccion": [[valor_pred]]
    }

@app.get("/historico/ultima_tmed")
def ultima_tmed(idema: str = Query(..., alias="id")):
    """Consulta la última tmed registrada para una estación."""
    try:
        with psycopg.connect(DSN) as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT fecha, tmed, nombre 
                    FROM datos_climaticos 
                    WHERE indicativo = %s AND tmed IS NOT NULL
                    ORDER BY fecha DESC
                    LIMIT 1;
                """
                cur.execute(query, (idema,))
                fila = cur.fetchone()

        if fila:
            return {"fecha": str(fila[0]), "tmed": float(fila[1]), "nombre": str(fila[2])}
        else:
            raise HTTPException(status_code=404, detail="No hay datos de tmed para esta estación")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en BD: {e}")
        raise HTTPException(status_code=500, detail="Error al conectar a la BD")

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
