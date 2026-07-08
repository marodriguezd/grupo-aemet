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

def entrenar_modelos():
    """Entrena los modelos estación por estación para no saturar la RAM."""
    asegurar_directorios()
    
    print("Conectando a AWS RDS para obtener lista de estaciones...")
    try:
        with psycopg.connect(DSN) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT DISTINCT indicativo FROM datos_climaticos;")
                estaciones = [row[0] for row in cur.fetchall()]
    except Exception as e:
        print(f"Error al conectar con AWS RDS: {e}")
        return

    print(f"\nSe encontraron {len(estaciones)} estaciones.")
    print("Iniciando entrenamiento masivo (cargando datos estación por estación para ahorrar RAM)...")
    
    estaciones_procesadas = 0
    
    for idema in estaciones:
        if not idema:
            continue
            
        idema_limpio = str(idema).strip().replace("/", "_").replace("\\", "_")
        
        # Obtenemos solo los datos de esta estación para que no explote la memoria RAM
        try:
            with psycopg.connect(DSN) as conn:
                with conn.cursor() as cur:
                    query = "SELECT tmed, tmax, tmin FROM datos_climaticos WHERE indicativo = %s ORDER BY fecha;"
                    cur.execute(query, (idema,))
                    data = cur.fetchall()
        except Exception as e:
            print(f"Error al descargar datos de la estación {idema}: {e}")
            continue
            
        if not data:
            continue
            
        df_bucle = pd.DataFrame(data, columns=["tmed", "tmax", "tmin"])
        
        # Asegurar tipos numéricos y quitar nulos
        df_bucle['tmed'] = pd.to_numeric(df_bucle['tmed'], errors='coerce')
        df_bucle['tmax'] = pd.to_numeric(df_bucle['tmax'], errors='coerce')
        df_bucle['tmin'] = pd.to_numeric(df_bucle['tmin'], errors='coerce')
        df_bucle = df_bucle.dropna()
        
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
        
        ruta_min = MODELOS_MIN_DIR / f"modelo_{idema_limpio}_min.pkl"
        with open(ruta_min, "wb") as f_min:
            pickle.dump(modelo_min, f_min)
            
        estaciones_procesadas += 1
        
        if estaciones_procesadas % 100 == 0:
            print(f"Progreso: {estaciones_procesadas} estaciones entrenadas...")
            
    print(f"\n¡Entrenamiento completado con éxito! Se han generado modelos para {estaciones_procesadas} estaciones.")

if __name__ == '__main__':
    entrenar_modelos()
