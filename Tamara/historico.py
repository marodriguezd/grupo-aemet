from datetime import date
from typing import List, Dict
import pandas as pd
from fastapi import HTTPException, Query, APIRouter
import psycopg


user = "postgres"
password = "postgres"
host = "localhost"
port = "5432"
database = "aemet"

dsn = f"postgresql://{user}:{password}@{host}:{port}/{database}"

with psycopg.connect(dsn) as conn:
    with conn.cursor() as cursor:

        cursor.execute("SELECT fecha, tmax, tmed, tmin, id  FROM datos_climaticos ORDER BY id;")
        data = cursor.fetchall()
      
        df_historico = pd.DataFrame(data=data, columns=["fecha", "tmax", "tmed", "tmin", "idema"])
        df_historico["fecha"] = pd.to_datetime(df_historico["fecha"]).dt.date

router_historico = APIRouter(prefix="/historico", tags=["historico"])

@router_historico.get(
    path="/obtener_historico",
    summary="Obtener histórico de temperaturas",
    description="Devuelve el histórico de temperaturas filtrado por estación y rango de fechas."
)
def obtener_historico(
    estacion_id: str = Query(..., alias="id", description="El ID de la estación (idema)"),
    fecha_inicio: date = Query(..., alias="fecha_inicio", description="Fecha de inicio del rango (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., alias="fecha_fin", description="Fecha de fin del rango (YYYY-MM-DD)")
):
    # 1. Validar orden de las fechas
    if fecha_inicio > fecha_fin:
        raise HTTPException(
            status_code=400, 
            detail="La fecha de inicio no puede ser posterior a la fecha de fin."
        )

  
    filtro = (
        (df_historico["idema"] == estacion_id) & 
        (df_historico["fecha"] >= fecha_inicio) & 
        (df_historico["fecha"] <= fecha_fin)
    )
    
    df_filtrado = df_historico[filtro]

    if df_filtrado.empty:
        return []

    df_filtrado = df_filtrado.copy()
    df_filtrado["fecha"] = df_filtrado["fecha"].astype(str)

   
    return df_filtrado.to_dict(orient="records")
