import json
import os

with open("App_Interactiva.ipynb", "r") as f:
    nb = json.load(f)

new_source = """%%writefile web_aemet.py
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
    \"\"\"
    Realiza una petición HTTP (GET o POST) con reintentos 
    en caso de error de conexión o timeout.
    \"\"\"
    for intento in range(max_reintentos):
        try:
            if metodo.upper() == 'POST':
                respuesta = requests.post(url, timeout=15, **kwargs)
            else:
                respuesta = requests.get(url, timeout=15, **kwargs)
            
            respuesta.raise_for_status() # Lanza error si status no es 200-299
            return respuesta
            
        except requests.exceptions.ConnectionError as e:
            print(f"Error de conexión con la API (Intento {intento + 1}/{max_reintentos}). Reintentando...")
            if intento < max_reintentos - 1:
                time.sleep(2) # Pausa antes del reintento
            else:
                raise # Lanza el error si se agotan los reintentos
        except requests.exceptions.Timeout as e:
            print(f"Tiempo de espera agotado (Intento {intento + 1}/{max_reintentos}). Reintentando...")
            if intento < max_reintentos - 1:
                time.sleep(2)
            else:
                raise

st.title("☀️ Panel de Control - AEMET")
st.text("Exploración de datos históricos y predicciones.")

with st.sidebar:
    st.header("Configuración")
    opcion = st.selectbox(
        "¿Qué quieres hacer?",
        ["Temperatura Máxima", "Temperatura Mínima", "Histórico"]
    )
    
if opcion in ["Temperatura Máxima", "Temperatura Mínima"]:
    st.header(f"Predicción de {opcion}")
    idema = st.text_input("Código de la estación (IDEMA):", value="0009X")
    valor = st.number_input("Valor numérico de entrada (ej. temperatura actual):", value=15.0)
    
    if st.button("Calcular"):
        with st.spinner("Conectando con la API..."):
            ruta = "modelos_max" if opcion == "Temperatura Máxima" else "modelos_min"
            url = f"{FASTAPI_URL}/{ruta}/{idema}/predict"
            
            try:
                res = realizar_peticion('POST', url, json={"features": [valor]})
                data = res.json()
                st.success(data["mensaje"])
                
                # Accedemos a la predicción simulada
                valor_pred = data["prediccion"][0][0]
                st.metric(label=f"Predicción ({idema})", value=f"{valor_pred:.2f} °C")
            except requests.exceptions.HTTPError as e:
                st.error(f"La API devolvió un error de servidor: {e}")
            except requests.exceptions.RequestException as e:
                st.error(f"Hubo un error al conectar con la API tras varios reintentos: {e}")

elif opcion == "Histórico":
    st.header("Histórico de Temperaturas")
    idema = st.text_input("Código IDEMA:", value="3195")
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

# Format into lines for the cell source
lines = new_source.split("\n")
formatted_lines = [line + "\n" for line in lines[:-1]] + [lines[-1]]

for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        source = cell.get("source", [])
        if len(source) > 0 and source[0].startswith("%%writefile web_aemet.py"):
            cell["source"] = formatted_lines
            break

with open("App_Interactiva.ipynb", "w") as f:
    json.dump(nb, f, indent=2)

print("Notebook actualizado.")
