import pandas as pd
import numpy as np

def limpiar_y_cargar_datos_fechas_todas_estaciones(datos_json):
    if not datos_json:
        return pd.DataFrame()
        
    datos_lista = []
    for dia in datos_json:
        datos_lista.append({ 
            "fecha"      : dia.get("fecha"),
            "indicativo" : dia.get("indicativo"),
            "nombre"     : dia.get("nombre"),
            "provincia"  : dia.get("provincia"),
            "altitud"    : dia.get("altitud"),
            "tmed"       : dia.get("tmed"),
            "prec"       : dia.get("prec"),
            "tmin"       : dia.get("tmin"),
            "horatmin"   : dia.get("horatmin"),
            "tmax"       : dia.get("tmax"),
            "horatmax"   : dia.get("horatmax"),
            "dir"        : dia.get("dir"),
            "velmedia"   : dia.get("velmedia"),
            "racha"      : dia.get("racha"),
            "horaracha"  : dia.get("horaracha"),
            "sol"        : dia.get("sol"),
            "presMax"    : dia.get("presMax"),
            "horaPresMax": dia.get("horaPresMax"),
            "presMin"    : dia.get("presMin"),
            "horaPresMin": dia.get("horaPresMin"),
            "hrMedia"    : dia.get("hrMedia"),
            "hrMax"      : dia.get("hrMax"),
            "horaHrMax"  : dia.get("horaHrMax"),
            "hrMin"      : dia.get("hrMin"),
            "horaHrMin"  : dia.get("horaHrMin")
        })

    df = pd.DataFrame(datos_lista)

    # 1. Ajustes básicos
    df["fecha"]      = pd.to_datetime(df["fecha"])
    df["altitud"]    = pd.to_numeric(df["altitud"], errors="coerce")
    df["indicativo"] = df["indicativo"].astype(str)
    df["nombre"]     = df["nombre"].astype(str)
    df["provincia"]  = df["provincia"].astype(str)
    df["dir"]        = df["dir"].astype(str)
    df["horaracha"]  = df["horaracha"].astype(str)

    def a_float(columna):
        if columna is None:
            return np.nan
        return columna.astype(str).str.replace(",", ".").replace("", "nan").astype(np.float32)

    # 2. Tipado numérico
    columnas_numericas = ["tmed", "tmin", "tmax", "velmedia", "racha", "sol", "presMax", "presMin", "hrMedia", "hrMax", "hrMin"]
    for col in columnas_numericas:
        if col in df.columns:
            df[col] = a_float(df[col])

    # 3. Precipitación (Ip -> 0.0)
    if "prec" in df.columns:
        df["prec"] = df["prec"].astype(str).str.replace("Ip", "0.0").str.replace(",", ".").replace("", "0.0")
        df["prec"] = pd.to_numeric(df["prec"], errors="coerce").astype(np.float32)

    # 4. Formatear horas
    columnas_tiempo = ["horatmin", "horatmax", "horaHrMax", "horaHrMin"]
    for col in columnas_tiempo:
        if col in df.columns:
            df[col] = df[col].astype(str).replace(["Varias", "nan", "None", ""], np.nan)
            df[col] = pd.to_datetime(df[col], format="%H:%M", errors="coerce").dt.time

    # 5. Otras horas
    columnas_hora_sola = ["horaPresMax", "horaPresMin"]
    for col in columnas_hora_sola:
        if col in df.columns:
            df[col] = df[col].astype(str).replace(["Varias", "nan", "None", ""], np.nan)
            df[col] = pd.to_datetime(df[col], format="%H", errors="coerce").dt.time

    # 6. Por nueva ubicacion de la estacion 7145D a 7145X, en el maestro de estaciones, ajustamos las mediciones.
    df["indicativo"] = df["indicativo"].replace("7145D", "7145X")        

    return df