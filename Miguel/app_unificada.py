# -*- coding: utf-8 -*-
"""
Frontend unificado con Streamlit.
Conecta con los modelos, el histórico y el asistente NLP de Gemini.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import date
import time

st.set_page_config(layout="wide", page_title="AEMET Unificada")
FASTAPI_URL = "http://127.0.0.1:8000"

def realizar_peticion(metodo, url, max_reintentos=3, **kwargs):
    """Realiza peticiones HTTP a la API con sistema de reintentos."""
    for intento in range(max_reintentos):
        try:
            if metodo.upper() == 'POST':
                respuesta = requests.post(url, timeout=30, **kwargs)
            else:
                respuesta = requests.get(url, timeout=30, **kwargs)
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
    """Descarga el catálogo de estaciones (cacheado 1 hora)."""
    try:
        res = requests.get(f"{FASTAPI_URL}/estaciones/lista", timeout=10)
        if res.status_code == 200:
            return res.json().get("estaciones", [])
    except:
        pass
    return []

st.title("Panel de Control Avanzado - AEMET")
st.markdown("Exploración de datos históricos, predicciones y **Asistente Inteligente NLP**.")

estaciones_db = obtener_estaciones()

with st.sidebar:
    st.header("Configuración")
    opcion = st.radio(
        "¿Qué quieres hacer?",
        ["Asistente Inteligente (NLP)", "Temperatura Máxima", "Temperatura Mínima", "Histórico"]
    )
    
def selector_estacion(key_suffix):
    if estaciones_db:
        opcion_busqueda = st.radio("Buscar estación por:", ["Selector por Nombre/Ciudad", "Código IDEMA manual"], key=f"radio_{key_suffix}")
        if opcion_busqueda == "Selector por Nombre/Ciudad":
            estacion = st.selectbox(
                "Selecciona o busca tu ciudad:", 
                estaciones_db, 
                format_func=lambda x: f"{x['nombre']} ({x['provincia']}) - {x['idema']}",
                index=None,
                placeholder="Escribe para buscar (ej. Sevilla, Barcelona)...",
                key=f"sel_{key_suffix}"
            )
            return estacion["idema"] if estacion else None
        else:
            return st.text_input("Código de la estación (IDEMA):", value="0009X", key=f"txt_{key_suffix}")
    else:
        return st.text_input("Código de la estación (IDEMA):", value="0009X", key=f"txt_{key_suffix}")

if opcion == "Asistente Inteligente (NLP)":
    st.header("Asistente Inteligente (Text-to-SQL)")
    st.markdown("Hazme cualquier pregunta en lenguaje natural sobre el clima y buscaré los datos en la base de datos.")
    
    pregunta = st.text_input(
        "Escribe tu pregunta:",
        placeholder="Ejemplo: Muéstrame la temperatura media máxima registrada en Madrid en el mes de agosto de 2024.",
        value="¿Cuál fue la temperatura máxima absoluta registrada en Barcelona durante julio de 2023?"
    )
    
    if st.button("Consultar Asistente"):
        with st.spinner("Gemini está pensando la consulta y conectando a RDS..."):
            try:
                res = realizar_peticion('POST', f"{FASTAPI_URL}/ask", json={"pregunta": pregunta})
                data = res.json()
                
                # Mostrar explicación
                st.success(data.get("explicacion", "Consulta realizada correctamente."))
                
                # Mostrar el código SQL generado
                with st.expander("Ver consulta SQL generada"):
                    st.code(data.get("sql_generado"), language="sql")
                
                # Mostrar los datos
                registros = data.get("datos", [])
                if registros:
                    df = pd.DataFrame(registros)
                    st.write(f"**Resultados Encontrados:** {len(registros)}")
                    
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("La consulta fue válida, pero no devolvió ningún registro de la base de datos.")
                    
            except requests.exceptions.HTTPError as e:
                # Tratar de leer el mensaje de error estructurado
                try:
                    error_json = e.response.json()
                    detail = error_json.get("detail", str(e))
                    st.error(f"Error de la API: {detail}")
                except:
                    st.error(f"Error HTTP devuelto por la API: {e}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error de conexión con el backend: {e}")


elif opcion in ["Temperatura Máxima", "Temperatura Mínima"]:
    st.header(f"Predicción de {opcion}")
    idema = selector_estacion("pred")
    
    st.write("---")
    modo_prediccion = st.radio("Método de entrada:", ["Usar última temperatura registrada", "Entrada Manual"])
    
    if modo_prediccion == "Entrada Manual":
        valor = st.number_input("Valor numérico de entrada (tmed actual):", value=15.0)
    else:
        st.info("Se buscará automáticamente la última temperatura media de esta estación en la base de datos.")
        valor = None
    
    if st.button("Calcular Predicción"):
        if not idema:
            st.warning("Por favor, selecciona una estación primero.")
            st.stop()
            
        with st.spinner("Conectando con la API..."):
            if modo_prediccion == "Usar última temperatura registrada":
                url_ultima = f"{FASTAPI_URL}/historico/ultima_tmed"
                try:
                    res_ult = realizar_peticion('GET', url_ultima, params={"id": idema})
                    data_ult = res_ult.json()
                    valor = data_ult["tmed"]
                    fecha_ult = data_ult["fecha"]
                    nombre_est = data_ult.get('nombre', 'Desconocida').title()
                    st.success(f"Última temperatura media registrada: {valor} °C (Fecha: {fecha_ult}) — {nombre_est} (IDEMA: {idema})")
                except requests.exceptions.HTTPError as e:
                    st.error("Error al obtener última temperatura: El servidor no tiene registros válidos recientes para esta estación.")
                    st.stop()
                except Exception as e:
                    st.error(f"Error de conexión: {e}")
                    st.stop()
                    
            ruta = "modelos_max" if opcion == "Temperatura Máxima" else "modelos_min"
            url = f"{FASTAPI_URL}/{ruta}/{idema}/predict"
            
            try:
                # Enviamos el 'valor' en formato POST JSON ya que la API espera un InputFeatures
                res = realizar_peticion('POST', url, json={"features": [valor]})
                data = res.json()
                st.success(data["mensaje"])
                
                valor_pred = data["prediccion"][0][0] if isinstance(data["prediccion"][0], list) else data["prediccion"][0]
                st.metric(label=f"Predicción ({idema})", value=f"{valor_pred:.2f} °C")
            except requests.exceptions.HTTPError as e:
                st.error("La API devolvió un error (Probablemente no hay modelo entrenado para esta estación).")
            except requests.exceptions.RequestException as e:
                st.error(f"Hubo un error al conectar con la API tras varios reintentos: {e}")

elif opcion == "Histórico":
    st.header("Histórico de Temperaturas")
    idema = selector_estacion("hist")
    
    col1, col2 = st.columns(2)
    with col1:
        f_ini = st.date_input("Fecha Inicio", value=date(2023, 1, 1))
    with col2:
        f_fin = st.date_input("Fecha Fin", value=date(2023, 1, 31))
        
    if st.button("Buscar Histórico"):
        if not idema:
            st.warning("Por favor, selecciona una estación primero.")
            st.stop()
            
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
                    
                    fig_hist = px.histogram(df, x=["tmax", "tmed", "tmin"], barmode="overlay", title="Distribución de Temperaturas")
                    st.plotly_chart(fig_hist, use_container_width=True)
                    
                    fig_box = px.box(df, y=["tmax", "tmed", "tmin"], title="Dispersión de Temperaturas")
                    st.plotly_chart(fig_box, use_container_width=True)
                    
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("No se encontraron datos para esas fechas.")
            except requests.exceptions.HTTPError as e:
                try:
                    error_msg = e.response.json().get('detail', str(e))
                except:
                    error_msg = e.response.text or str(e)
                st.error(f"La API devolvió un error: {error_msg}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error al conectar o consultar el histórico tras varios reintentos: {e}")
