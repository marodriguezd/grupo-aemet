# -*- coding: utf-8 -*-
"""
API backend con FastAPI para predicciones y consulta histórica.
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import psycopg
from datetime import date

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

@app.post("/modelos_max/{idema}/predict")
def prediccion_temp_max(idema: str, input_data: InputFeatures):
    """Simula una predicción de temperatura máxima."""
    print(f"Calculando temp máxima para {idema}...")
    valor_simulado = input_data.features[0] * 1.5 + 5.0
    return {
        "status": "success",
        "idema": idema,
        "mensaje": "Predicción de temperatura máxima calculada",
        "prediccion": [[valor_simulado]]
    }

@app.post("/modelos_min/{idema}/predict")
def prediccion_temp_min(idema: str, input_data: InputFeatures):
    """Simula una predicción de temperatura mínima."""
    print(f"Calculando temp mínima para {idema}...")
    valor_simulado = input_data.features[0] * 0.8 - 2.0
    return {
        "status": "success",
        "idema": idema,
        "mensaje": "Predicción de temperatura mínima calculada",
        "prediccion": [[valor_simulado]]
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


