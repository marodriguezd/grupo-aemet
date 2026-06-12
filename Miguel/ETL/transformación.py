# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np

# Limpieza y preparación de los datos obtenidos en formato JSON
def limpiar_y_cargar_datos(datos_json):
    if not datos_json:
        return pd.DataFrame()
        
    datos_lista = []
    for dia in datos_json:
        datos_lista.append({
            "fecha": dia.get("fecha"),
            "indicativo": dia.get("indicativo"),
            "nombre": dia.get("nombre"),
            "provincia": dia.get("provincia"),
            "altitud": dia.get("altitud"),
            "tmed": dia.get("tmed"),
            "prec": dia.get("prec", "0,00"),
            "tmin": dia.get("tmin"),
            "horatmin": dia.get("horatmin"),
            "tmax": dia.get("tmax"),
            "horatmax": dia.get("horatmax"),
            "dir": dia.get("dir"),
            "velmedia": dia.get("velmedia"),
            "racha": dia.get("racha"),
            "horaracha": dia.get("horaracha"),
            "sol": dia.get("sol"),
            "presMax": dia.get("presMax"),
            "horaPresMax": dia.get("horaPresMax"),
            "presMin": dia.get("presMin"),
            "horaPresMin": dia.get("horaPresMin"),
            "hrMedia": dia.get("hrMedia"),
            "hrMax": dia.get("hrMax"),
            "horaHrMax": dia.get("horaHrMax"),
            "hrMin": dia.get("hrMin"),
            "horaHrMin": dia.get("horaHrMin")
        })

    df = pd.DataFrame(datos_lista)

    # 1. Ajustes básicos de tipos de datos comunes
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["indicativo"] = df["indicativo"].astype(str)
    df["nombre"] = df["nombre"].astype(str)
    df["provincia"] = df["provincia"].astype(str)
    df["altitud"] = pd.to_numeric(df["altitud"], errors="coerce")

    # Función interna para pasar números con coma (formato español) a float con punto (formato estándar)
    def a_float(columna):
        if columna is None:
            return np.nan
        return columna.astype(str).str.replace(",", ".").replace("", "nan").astype(np.float32)

    # 2. Convertimos las columnas numéricas que tienen comas
    columnas_numericas = ["tmed", "tmin", "tmax", "velmedia", "racha", "sol", "presMax", "presMin", "hrMedia", "hrMax", "hrMin"]
    for col in columnas_numericas:
        if col in df.columns:
            df[col] = a_float(df[col])

    # 3. Arreglamos la precipitación (la API a veces devuelve "Ip" que significa inapreciable, la ponemos en 0.0)
    if "prec" in df.columns:
        df["prec"] = df["prec"].astype(str).str.replace("Ip", "0.0").str.replace(",", ".").replace("", "0.0")
        df["prec"] = pd.to_numeric(df["prec"], errors="coerce").astype(np.float32)

    # 4. Limpiamos las horas y las pasamos a tipo time de python (HH:MM)
    columnas_tiempo = ["horatmin", "horatmax", "horaHrMax", "horaHrMin"]
    for col in columnas_tiempo:
        if col in df.columns:
            df[col] = df[col].astype(str).replace(["Varias", "nan", "None", ""], np.nan)
            df[col] = pd.to_datetime(df[col], format="%H:%M", errors="coerce").dt.time

    # 5. Otras horas que vienen representadas solo con la hora (HH)
    columnas_hora_sola = ["horaPresMax", "horaPresMin"]
    for col in columnas_hora_sola:
        if col in df.columns:
            df[col] = df[col].astype(str).replace(["Varias", "nan", "None", ""], np.nan)
            df[col] = pd.to_datetime(df[col], format="%H", errors="coerce").dt.time

    if "dir" in df.columns:
        df["dir"] = df["dir"].astype(str)
    if "horaracha" in df.columns:
        df["horaracha"] = df["horaracha"].astype(str)

    return df
