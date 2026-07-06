# -*- coding: utf-8 -*-
"""
Frontend con Streamlit.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import date

st.set_page_config(layout="wide")
FASTAPI_URL = "http://127.0.0.1:8000"

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
            res = requests.post(url, json={"features": [valor]})

            if res.status_code == 200:
                data = res.json()
                st.success(data["mensaje"])

                # Accedemos a la predicción simulada
                valor_pred = data["prediccion"][0][0]
                st.metric(label=f"Predicción ({idema})", value=f"{valor_pred:.2f} °C")
            else:
                st.error("Hubo un error al conectar con la API.")

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
            res = requests.get(url, params={"id": idema, "fecha_inicio": f_ini, "fecha_fin": f_fin})

            if res.status_code == 200:
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
            else:
                st.error("Error al consultar el histórico.")


