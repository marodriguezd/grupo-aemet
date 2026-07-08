import json

with open("App_Interactiva.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

API_CODE = """%%writefile api_aemet.py
# -*- coding: utf-8 -*-
\"\"\"
API backend con FastAPI para predicciones y consulta histórica.
\"\"\"

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
    \"\"\"Devuelve la lista completa de estaciones disponibles.\"\"\"
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
    \"\"\"Predicción real de temperatura máxima con XGBoost.\"\"\"
    idema_limpio = idema.strip().replace("/", "_").replace("\\\\", "_")
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
    \"\"\"Predicción real de temperatura mínima con XGBoost.\"\"\"
    idema_limpio = idema.strip().replace("/", "_").replace("\\\\", "_")
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
    \"\"\"Consulta la última tmed registrada para una estación.\"\"\"
    try:
        with psycopg.connect(DSN) as conn:
            with conn.cursor() as cur:
                query = \"\"\"
                    SELECT fecha, tmed 
                    FROM datos_climaticos 
                    WHERE indicativo = %s AND tmed IS NOT NULL
                    ORDER BY fecha DESC
                    LIMIT 1;
                \"\"\"
                cur.execute(query, (idema,))
                fila = cur.fetchone()
                
        if fila:
            return {"fecha": str(fila[0]), "tmed": float(fila[1])}
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
    \"\"\"Consulta el histórico directamente a la base de datos.\"\"\"
    if fecha_inicio > fecha_fin:
        raise HTTPException(status_code=400, detail="Fechas incorrectas")
        
    print(f"Consultando histórico de {idema}...")
    try:
        with psycopg.connect(DSN) as conn:
            with conn.cursor() as cur:
                query = \"\"\"
                    SELECT fecha, tmax, tmed, tmin 
                    FROM datos_climaticos 
                    WHERE indicativo = %s AND fecha >= %s AND fecha <= %s
                    ORDER BY fecha;
                \"\"\"
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
"""

WEB_CODE = """%%writefile web_aemet.py
# -*- coding: utf-8 -*-
\"\"\"
Frontend con Streamlit.
\"\"\"

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import date
import time

st.set_page_config(layout="wide")
FASTAPI_URL = "http://127.0.0.1:8000"

def realizar_peticion(metodo, url, max_reintentos=3, **kwargs):
    for intento in range(max_reintentos):
        try:
            if metodo.upper() == 'POST':
                respuesta = requests.post(url, timeout=15, **kwargs)
            else:
                respuesta = requests.get(url, timeout=15, **kwargs)
            respuesta.raise_for_status()
            return respuesta
        except requests.exceptions.ConnectionError:
            if intento < max_reintentos - 1:
                time.sleep(2)
            else:
                raise
        except requests.exceptions.Timeout:
            if intento < max_reintentos - 1:
                time.sleep(2)
            else:
                raise

@st.cache_data(ttl=3600)
def obtener_estaciones():
    try:
        res = requests.get(f"{FASTAPI_URL}/estaciones/lista", timeout=10)
        if res.status_code == 200:
            return res.json().get("estaciones", [])
    except:
        pass
    return []

st.title("☀️ Panel de Control - AEMET")
st.text("Exploración de datos históricos y predicciones.")

estaciones_db = obtener_estaciones()

with st.sidebar:
    st.header("Configuración")
    opcion = st.selectbox(
        "¿Qué quieres hacer?",
        ["Temperatura Máxima", "Temperatura Mínima", "Histórico"]
    )
    
def selector_estacion(key_suffix):
    if estaciones_db:
        opcion_busqueda = st.radio("Buscar estación por:", ["Selector por Nombre/Ciudad", "Código IDEMA manual"], key=f"radio_{key_suffix}")
        if opcion_busqueda == "Selector por Nombre/Ciudad":
            estacion = st.selectbox(
                "Selecciona o busca tu ciudad:", 
                estaciones_db, 
                format_func=lambda x: f"{x['nombre']} ({x['provincia']}) - {x['idema']}",
                key=f"sel_{key_suffix}"
            )
            return estacion["idema"]
        else:
            return st.text_input("Código de la estación (IDEMA):", value="0009X", key=f"txt_{key_suffix}")
    else:
        return st.text_input("Código de la estación (IDEMA):", value="0009X", key=f"txt_{key_suffix}")

if opcion in ["Temperatura Máxima", "Temperatura Mínima"]:
    st.header(f"Predicción de {opcion}")
    idema = selector_estacion("pred")
    
    st.write("---")
    modo_prediccion = st.radio("Método de entrada:", ["Entrada Manual", "Usar última temperatura registrada"])
    
    if modo_prediccion == "Entrada Manual":
        valor = st.number_input("Valor numérico de entrada (tmed actual):", value=15.0)
    else:
        st.info("Se buscará automáticamente la última temperatura media de esta estación en la base de datos.")
        valor = None
    
    if st.button("Calcular"):
        with st.spinner("Conectando con la API..."):
            if modo_prediccion == "Usar última temperatura registrada":
                url_ultima = f"{FASTAPI_URL}/historico/ultima_tmed"
                try:
                    res_ult = realizar_peticion('GET', url_ultima, params={"id": idema})
                    data_ult = res_ult.json()
                    valor = data_ult["tmed"]
                    fecha_ult = data_ult["fecha"]
                    st.success(f"Última temperatura media registrada: {valor} °C (Fecha: {fecha_ult})")
                except requests.exceptions.HTTPError as e:
                    st.error(f"Error al obtener última temperatura: El servidor no tiene registros válidos recientes para esta estación.")
                    st.stop()
                except Exception as e:
                    st.error(f"Error de conexión: {e}")
                    st.stop()
                    
            ruta = "modelos_max" if opcion == "Temperatura Máxima" else "modelos_min"
            url = f"{FASTAPI_URL}/{ruta}/{idema}/predict"
            
            try:
                res = realizar_peticion('POST', url, json={"features": [valor]})
                data = res.json()
                st.success(data["mensaje"])
                
                valor_pred = data["prediccion"][0][0]
                st.metric(label=f"Predicción ({idema})", value=f"{valor_pred:.2f} °C")
            except requests.exceptions.HTTPError as e:
                st.error(f"La API devolvió un error (Probablemente no hay modelo para esta estación).")
            except requests.exceptions.RequestException as e:
                st.error(f"Hubo un error al conectar con la API tras varios reintentos: {e}")

elif opcion == "Histórico":
    st.header("Histórico de Temperaturas")
    idema = selector_estacion("hist")
    
    col1, col2 = st.columns(2)
    with col1:
        f_ini = st.date_input("Fecha Inicio", value=date(2020, 1, 1))
    with col2:
        f_fin = st.date_input("Fecha Fin", value=date(2020, 1, 31))
        
    if st.button("Buscar"):
        with st.spinner("Buscando en la base de datos..."):
            url = f"{FASTAPI_URL}/historico/obtener_historico"
            
            try:
                res = realizar_peticion('GET', url, params={"id": idema, "fecha_inicio": f_ini, "fecha_fin": f_fin})
                data = res.json()
                registros = data.get("registros", [])
                if registros:
                    df = pd.DataFrame(registros)
                    df["fecha"] = pd.to_datetime(df["fecha"])
                    fig = px.line(df, x="fecha", y=["tmax", "tmed", "tmin"], title="Evolución de Temperaturas", markers=True)
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(df)
                else:
                    st.warning("No se encontraron datos para esas fechas.")
            except requests.exceptions.HTTPError as e:
                st.error(f"La API devolvió un error: {e}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error al conectar o consultar el histórico tras varios reintentos: {e}")
"""

for cell in nb["cells"]:
    if cell["cell_type"] != "code" or not cell["source"]: continue
    
    if "%%writefile api_aemet.py\n" in cell["source"][0] or "%%writefile api_aemet.py" in cell["source"][0]:
        cell["source"] = [line + "\\n" for line in API_CODE.split("\\n")]
        cell["source"][-1] = cell["source"][-1].rstrip("\\n")
        
    if "%%writefile web_aemet.py\n" in cell["source"][0] or "%%writefile web_aemet.py" in cell["source"][0]:
        cell["source"] = [line + "\\n" for line in WEB_CODE.split("\\n")]
        cell["source"][-1] = cell["source"][-1].rstrip("\\n")

with open("App_Interactiva.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2, ensure_ascii=False)
