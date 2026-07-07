import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import psycopg
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import httpx
import streamlit as st
import requests
import pandas as pd
from datetime import date




user = "postgres"
password = "postgres"
host = "localhost"
port = "5432"
database = "aemet"


dsn = f"postgresql://{user}:{password}@{host}:{port}/{database}"

print(dsn)


# ====================================================================
# INSTRUCCIONES DE EJECUCIÓN:
# 1. Abre tu terminal en la carpeta donde está este script.
# 2. Ejecuta el siguiente comando:
#    streamlit run app_aemet.py
# 3. Se abrirá automáticamente una pestaña en tu navegador web.



st.set_page_config(layout="wide")

FASTAPI_URL = "http://localhost:8000"

with st.sidebar:
    st.header("Configuración de Consulta")
    
    opcion = st.selectbox(
        "Selecciona el tipo de consulta:",
        ["Temperatura Máxima", "Temperatura Mínima", "Histórico"]
    )
    
    st.divider()

    if opcion == "Temperatura Máxima":
        st.subheader("Parámetros: Temp. Máxima")
        idema = st.text_input("Código de la estación (IDEMA):", value="0009X")
        st.markdown("**Características para el modelo:**")
        ejecutar_consulta = st.button("Generar Predicción Máxima")
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cursor:

                cursor.execute(query = f"""SELECT tmax FROM datos_climaticos WHERE id = '{idema}' ORDER BY fecha DESC LIMIT 1;""")
                input_data = cursor.fetchall()[0][0]


    elif opcion == "Temperatura Mínima":
        st.subheader("Parámetros: Temp. Mínima")
        idema = st.text_input("Código de la estación (IDEMA):", value="0009X")
        st.markdown("**Características para el modelo:**")
        ejecutar_consulta = st.button("Generar Predicción Mínima")
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cursor:

                cursor.execute(query = f"""SELECT tmin FROM datos_climaticos WHERE id = '{idema}' ORDER BY fecha DESC LIMIT 1;""")
                input_data = cursor.fetchall()[0][0]

    elif opcion == "Histórico":
        st.subheader("Parámetros: Histórico")
        idema = st.text_input("Código de la estación (IDEMA):", value="0009X")
        fecha_inicio = st.date_input("Fecha de inicio:", value=date(2025, 1, 1))
        fecha_fin = st.date_input("Fecha de fin:", value=date(2025, 1, 31))
        ejecutar_consulta = st.button("Consultar Histórico")

st.title("Panel de Control - AEMET")
st.text("Exploración de datos históricos de temperaturas y ejecución de predicciones basadas en modelos entrenados.")
st.divider()

if opcion == "Temperatura Máxima":
    st.header("Predicción de Temperatura Máxima")
    
    if ejecutar_consulta:
        with st.spinner("Ejecutando modelo de predicción máxima..."):
            try:
                lista_features = [float(input_data)]
                payload = {"features": lista_features}
                
                enlace_completo = f"{FASTAPI_URL}/modelos_max/{idema}/predict" 
                res = requests.post(enlace_completo, json=payload)
                
                if res.status_code == 200:
                    data = res.json()
                    st.success(data["mensaje"])
                    
                    valor_predicho = data["prediccion"]
                    if isinstance(valor_predicho, list): valor_predicho = valor_predicho[0]
                    if isinstance(valor_predicho, list): valor_predicho = valor_predicho[0]
                    
                    st.metric(label=f"Predicción Máxima ({data['idema']})", value=f"{valor_predicho:.2f} °C")
                        
                    with st.expander("Ver respuesta completa de la API"):
                        st.json(data)
                else:
                    error_data = res.json()
                    st.error(f"Error {res.status_code}: {error_data.get('detail', 'Error desconocido')}")
            except ValueError:
                st.error("Por favor, asegúrate de introducir un valor numérico válido.")
            except Exception as e:
                st.error(f"Error inesperado: {e}")

elif opcion == "Temperatura Mínima":
    st.header("Predicción de Temperatura Mínima")
    
    if ejecutar_consulta:
        with st.spinner("Ejecutando modelo de predicción mínima..."):
            try:
                lista_features = [float(input_data)]
                payload = {"features": lista_features}
                
                enlace_completo = f"{FASTAPI_URL}/modelos_min/{idema}/predict" 
                res = requests.post(enlace_completo, json=payload)
                
                if res.status_code == 200:
                    data = res.json()
                    st.success(data["mensaje"])
                    
                    valor_predicho = data["prediccion"]
                    if isinstance(valor_predicho, list): valor_predicho = valor_predicho[0]
                    if isinstance(valor_predicho, list): valor_predicho = valor_predicho[0]
                    
                    st.metric(label=f"Predicción Mínima ({data['idema']})", value=f"{valor_predicho:.2f} °C")
                        
                    with st.expander("Ver respuesta completa de la API"):
                        st.json(data)
                else:
                    error_data = res.json()
                    st.error(f"Error {res.status_code}: {error_data.get('detail', 'Error desconocido')}")
            except ValueError:
                st.error("Por favor, asegúrate de introducir un valor numérico válido.")
            except Exception as e:
                st.error(f"Error inesperado: {e}")

elif opcion == "Histórico":
    st.header("Consulta de Registros Históricos")
    
    if ejecutar_consulta:
        with st.spinner("Consultando base de datos a través de FastAPI..."):
            try:
                str_inicio = fecha_inicio.strftime("%Y-%m-%d")
                str_fin = fecha_fin.strftime("%Y-%m-%d")
                
                enlace_completo = f"{FASTAPI_URL}/historico/obtener_historico?id={idema}&fecha_inicio={str_inicio}&fecha_fin={str_fin}" 
                res = requests.get(enlace_completo) 
                
                if res.status_code == 200:
                    data = res.json()
                    st.success("Registros históricos recuperados de forma exitosa.")
                    
                    if "registros" in data:
                        df_historico = pd.DataFrame(data["registros"])
                        df_historico["fecha"] = pd.to_datetime(df_historico["fecha"])
                        
                        st.subheader(f"Evolución Climatológica de la Estación {idema}")
                        st.line_chart(df_historico, x="fecha", y=["tmax", "tmed", "tmin"])
                        
                        with st.expander("Ver tabla completa de registros filtrados"):
                            st.dataframe(df_historico, use_container_width=True)
                            
                        with st.expander("Ver respuesta completa de la API"):
                            st.json(data)
                    else:
                        st.info("Visualización genérica del diccionario de datos recibido:")
                        st.json(data)
                else:
                    error_data = res.json()
                    st.error(f"Error {res.status_code}: {error_data.get('detail', 'Error desconocido')}")
            except Exception as e:
                st.error(f"Error inesperado en la aplicación: {e}")
