# -*- coding: utf-8 -*-
"""
Este módulo entrena los modelos de Machine Learning (XGBoost) para cada
estación meteorológica (idema) basándose en los históricos consolidados
en CSV, generando y guardando los archivos .pkl listos para usarse.
"""

import os
import sys
import glob
import pickle
import psycopg
import pandas as pd
import numpy as np
import xgboost as xgb
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import root_mean_squared_error

# ---- Constantes de rutas ----
# Obtenemos la ruta absoluta de la carpeta 'Miguel' (padre de ETL)
MIGUEL_DIR = Path(__file__).resolve().parent.parent
CSV_DIR = MIGUEL_DIR / "sheets" / "csv"
MODELOS_MAX_DIR = MIGUEL_DIR / "modelos_max"
MODELOS_MIN_DIR = MIGUEL_DIR / "modelos_min"

# ---- Credenciales de AWS RDS ----
HOST = "database-dai07rt-proyecto-aemet-2026.cr828ecqk1a6.eu-central-1.rds.amazonaws.com"
PORT = "5432"
DBNAME = "postgres"
USER = "aemet2026"
PASSWORD = "mondongo-dai07rt-aemet-2026"
DSN = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"

def asegurar_directorios():
    """Crea los directorios de destino si no existen."""
    os.makedirs(MODELOS_MAX_DIR, exist_ok=True)
    os.makedirs(MODELOS_MIN_DIR, exist_ok=True)
    print(f"Directorios de salida verificados:\n- {MODELOS_MAX_DIR}\n- {MODELOS_MIN_DIR}")

def cargar_datos_rds():
    """Conecta a la base de datos AWS RDS y extrae el histórico completo."""
    print("Conectando a AWS RDS...")
    try:
        with psycopg.connect(DSN) as conn:
            with conn.cursor() as cur:
                print("Descargando datos históricos (esto puede tardar unos minutos)...")
                query = "SELECT indicativo as id, tmed, tmax, tmin FROM datos_climaticos order by fecha;"
                cur.execute(query)
                data = cur.fetchall()
                
        df_completo = pd.DataFrame(data, columns=["id", "tmed", "tmax", "tmin"])
        
        # Asegurar tipos numéricos por si vienen como texto desde la BD
        df_completo['tmed'] = pd.to_numeric(df_completo['tmed'], errors='coerce')
        df_completo['tmax'] = pd.to_numeric(df_completo['tmax'], errors='coerce')
        df_completo['tmin'] = pd.to_numeric(df_completo['tmin'], errors='coerce')
        
        print(f"\nSe han cargado un total de {len(df_completo)} registros desde la nube de AWS.")
        return df_completo
    except Exception as e:
        print(f"Error al conectar con AWS RDS: {e}")
        return pd.DataFrame()

def entrenar_modelos():
    """Agrupa por estación y entrena los modelos de temp máxima y mínima."""
    df = cargar_datos_rds()
    if df.empty:
        return
    
    asegurar_directorios()
    
    # Nos quedamos con las columnas que nos importan
    cols_necesarias = ["id", "tmed", "tmax", "tmin"]
    if not all(col in df.columns for col in cols_necesarias):
        print("Faltan columnas necesarias en los datos CSV.")
        return
        
    estaciones_procesadas = 0
    print("\nIniciando entrenamiento masivo de modelos por estación...")
    
    estaciones_unicas = df["id"].unique()
    for idema in estaciones_unicas:
        idema_limpio = str(idema).strip().replace("/", "_").replace("\\", "_")
        
        # Filtramos por estación y eliminamos filas con Nulos en las variables clave
        df_bucle = df[df["id"] == idema][cols_necesarias].dropna()
        
        # Necesitamos un mínimo de datos (ej: 5) para que XGBoost no falle
        if len(df_bucle) < 5:
            continue
            
        # -- ENTRENAMIENTO TEMPERATURA MÁXIMA --
        X_max = df_bucle[["tmed"]]
        y_max = df_bucle["tmax"]
        
        X_train_max, X_test_max, y_train_max, y_test_max = train_test_split(
            X_max, y_max, test_size=0.2, random_state=42
        )
        
        modelo_max = xgb.XGBRegressor(random_state=42, n_estimators=200, learning_rate=0.01)
        modelo_max.fit(X_train_max, y_train_max)
        
        # Guardar archivo .pkl
        ruta_max = MODELOS_MAX_DIR / f"modelo_{idema_limpio}_max.pkl"
        with open(ruta_max, "wb") as f_max:
            pickle.dump(modelo_max, f_max)
            
        # -- ENTRENAMIENTO TEMPERATURA MÍNIMA --
        X_min = df_bucle[["tmed"]]
        y_min = df_bucle["tmin"]
        
        X_train_min, X_test_min, y_train_min, y_test_min = train_test_split(
            X_min, y_min, test_size=0.2, random_state=42
        )
        
        modelo_min = xgb.XGBRegressor(random_state=42, n_estimators=200, learning_rate=0.01)
        modelo_min.fit(X_train_min, y_train_min)
        
        # Guardar archivo .pkl
        ruta_min = MODELOS_MIN_DIR / f"modelo_{idema_limpio}_min.pkl"
        with open(ruta_min, "wb") as f_min:
            pickle.dump(modelo_min, f_min)
            
        estaciones_procesadas += 1
        
        if estaciones_procesadas % 100 == 0:
            print(f"Progreso: {estaciones_procesadas} estaciones entrenadas...")
            
    print(f"\n¡Entrenamiento completado con éxito! Se han generado modelos para {estaciones_procesadas} estaciones.")

if __name__ == '__main__':
    entrenar_modelos()
