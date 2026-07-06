from datetime import date
from typing import List, Dict
import pandas as pd
from fastapi import HTTPException, Query, APIRouter
import psycopg

router_historico = APIRouter(prefix="/historico", tags=["historico"])

# Credenciales de BD AWS RDS (Actualizado)
HOST = "database-dai07rt-proyecto-aemet-2026.cr828ecqk1a6.eu-central-1.rds.amazonaws.com"
PORT = "5432"
DBNAME = "postgres"
USER = "aemet2026"
PASSWORD = "mondongo-dai07rt-aemet-2026"
DSN = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"

@router_historico.get(
    path="/obtener_historico",
    summary="Obtener histórico de temperaturas",
    description="Devuelve el histórico de temperaturas filtrado por estación y rango de fechas consultando directamente la BD."
)
def obtener_historico(
    estacion_id: str = Query(..., alias="id", description="El ID de la estación (idema)"),
    fecha_inicio: date = Query(..., alias="fecha_inicio", description="Fecha de inicio del rango (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., alias="fecha_fin", description="Fecha de fin del rango (YYYY-MM-DD)")
):
    if fecha_inicio > fecha_fin:
        raise HTTPException(
            status_code=400, 
            detail="La fecha de inicio no puede ser posterior a la fecha de fin."
        )

    try:
        # Hacemos la consulta directamente para no sobrecargar la RAM
        with psycopg.connect(DSN) as conn:
            with conn.cursor() as cursor:
                # Usamos 'indicativo' que es el nombre real de la columna en AWS
                query = """
                    SELECT fecha, tmax, tmed, tmin 
                    FROM datos_climaticos 
                    WHERE indicativo = %s AND fecha >= %s AND fecha <= %s
                    ORDER BY fecha;
                """
                cursor.execute(query, (estacion_id, fecha_inicio, fecha_fin))
                data = cursor.fetchall()
        
        if not data:
            return []
            
        df_historico = pd.DataFrame(data=data, columns=["fecha", "tmax", "tmed", "tmin"])
        df_historico["fecha"] = pd.to_datetime(df_historico["fecha"]).dt.date.astype(str)
        
        return {"registros": df_historico.to_dict(orient="records")}

    except Exception as e:
        print(f"Error en base de datos: {e}")
        raise HTTPException(status_code=500, detail="Error al conectar o consultar la base de datos.")
