# -*- coding: utf-8 -*-
import os
import sys
import time
import gc
import zipfile
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Tuve que meter este parche raro de zipfile porque da error al cerrar archivos excel en python 3.14+
# 'ValueError: seek of closed file'. Evita que se raye si se ejecuta varias veces.
if not hasattr(zipfile.ZipFile, '_patched'):
    try:
        _orig_zipfile_del = zipfile.ZipFile.__del__
        def _safe_zipfile_del(self):
            try:
                _orig_zipfile_del(self)
            except (ValueError, AttributeError):
                pass
        zipfile.ZipFile.__del__ = _safe_zipfile_del
        zipfile.ZipFile._patched = True
    except AttributeError:
        pass

# Añadimos la ruta de este script para poder importar los módulos locales sin líos de path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extracción import obtener_valores_climaticos_todas
from transformación import limpiar_y_cargar_datos

# Configuración de rutas relativas a la carpeta Miguel
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_CSV_DIR = BASE_DIR / 'sheets' / 'csv'
OUTPUT_XLSX_DIR = BASE_DIR / 'sheets' / 'xlsx'

# Función para escanear los archivos y encontrar la última fecha guardada
def obtener_ultima_fecha_existente():
    if not OUTPUT_CSV_DIR.exists():
        return None

    # Buscamos archivos del tipo climaticos_YYYY.csv
    archivos = list(OUTPUT_CSV_DIR.glob("climaticos_*.csv"))
    if not archivos:
        return None

    años = []
    for f in archivos:
        try:
            # Sacamos el año a partir del nombre del archivo (climaticos_2026.csv -> 2026)
            anio = int(f.stem.split("_")[1])
            años.append((anio, f))
        except (IndexError, ValueError):
            continue

    if not años:
        return None

    # Ordenamos para quedarnos con el año más nuevo
    años.sort(key=lambda x: x[0], reverse=True)
    ultimo_anio, ruta_archivo = años[0]

    print(f"Detectado archivo del año más reciente: {ruta_archivo.name}")

    try:
        # Cargamos solo la columna fecha para no consumir mucha RAM
        df = pd.read_csv(ruta_archivo, usecols=["fecha"])
        if df.empty or "fecha" not in df.columns:
            return None
        
        # Buscamos la fecha máxima
        fechas = pd.to_datetime(df["fecha"])
        ultima_fecha = fechas.max()
        return ultima_fecha.to_pydatetime()
    except Exception as e:
        print(f"Error al leer la última fecha del archivo {ruta_archivo.name}: {e}")
        return None

# Función para fusionar los datos nuevos con los existentes, quitar duplicados y guardar
def integrar_y_guardar_datos(df_lote, anio):
    if df_lote.empty:
        return

    csv_path = OUTPUT_CSV_DIR / f'climaticos_{anio}.csv'
    excel_path = OUTPUT_XLSX_DIR / f'climaticos_{anio}.xlsx'

    # Si ya existe el archivo del año, cargamos los datos viejos para sumarlos
    if csv_path.exists():
        print(f"Cargando datos existentes del año {anio} desde CSV para fusionar...")
        try:
            df_existente = pd.read_csv(csv_path)
            # Aseguramos que la columna fecha sea tipo datetime en ambos
            df_existente["fecha"] = pd.to_datetime(df_existente["fecha"])
            df_lote["fecha"] = pd.to_datetime(df_lote["fecha"])
            
            # Concatenamos la información antigua y la nueva
            df_combinado = pd.concat([df_existente, df_lote], ignore_index=True)
        except Exception as e:
            print(f"Error al leer el CSV existente de {anio}: {e}. Sobreescribiendo con los datos nuevos...")
            df_combinado = df_lote
    else:
        df_combinado = df_lote

    # Eliminamos duplicados por fecha y estación (indicativo).
    # Conservamos el último que hayamos descargado por si acaso.
    df_combinado = df_combinado.drop_duplicates(subset=["fecha", "indicativo"], keep="last")

    # Ordenamos cronológicamente (más antiguo a más reciente)
    df_combinado = df_combinado.sort_values(by="fecha", ascending=True)

    # Nos aseguramos de crear las carpetas si no existen
    OUTPUT_CSV_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_XLSX_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Guardando ficheros actualizados para el año {anio} (Registros totales: {len(df_combinado)})...")
    try:
        # Guardamos en CSV
        df_combinado.to_csv(csv_path, index=False)
        print(f"Guardado CSV en: {csv_path}")

        # Guardamos en Excel con openpyxl
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df_combinado.to_excel(writer, index=False)
        print(f"Guardado Excel en: {excel_path}")
    except Exception as e:
        print(f"Error al guardar los archivos de {anio}: {e}")

# Orquestador del flujo ETL completo con soporte incremental
def ejecutar_etl(dias_defecto_historico=3650):
    print("Buscando última fecha cargada en disco...")
    ultima_fecha = obtener_ultima_fecha_existente()

    if ultima_fecha:
        # Modo incremental
        fecha_inicio = ultima_fecha + timedelta(days=1)
        # Consultamos hasta hoy
        fecha_fin = datetime.now()
        
        # Si ya estamos al día, paramos
        if fecha_inicio.date() > fecha_fin.date():
            print(f"¡Todo al día! La última fecha en disco es {ultima_fecha.strftime('%Y-%m-%d')} y hoy es {fecha_fin.strftime('%Y-%m-%d')}.")
            return
            
        print(f"Modo incremental activado. Descargando datos desde {fecha_inicio.strftime('%Y-%m-%d')} hasta {fecha_fin.strftime('%Y-%m-%d')}...")
    else:
        # Carga histórica inicial de 10 años por defecto (hasta el límite teórico del notebook original)
        fecha_fin = datetime(2026, 5, 30)
        fecha_inicio = fecha_fin - timedelta(days=dias_defecto_historico - 1)
        print(f"No se detectaron archivos previos. Iniciando carga histórica por defecto desde {fecha_inicio.strftime('%Y-%m-%d')} hasta {fecha_fin.strftime('%Y-%m-%d')}...")

    # Realizamos la descarga en bloques de 15 días
    fecha_actual = fecha_fin
    lote_size = 15
    total_dias = (fecha_fin - fecha_inicio).days + 1
    dias_procesados = 0

    print(f"Rango de descarga: {total_dias} días totales en bloques de {lote_size} días.")

    while dias_procesados < total_dias:
        dias_restantes = total_dias - dias_procesados
        dias_lote = min(lote_size, dias_restantes)

        fecha_ini_lote = fecha_actual - timedelta(days=dias_lote - 1)

        fecha_ini_str = fecha_ini_lote.strftime("%Y-%m-%dT00:00:00UTC")
        fecha_fin_str = fecha_actual.strftime("%Y-%m-%dT23:59:59UTC")

        print(f"\nDescargando bloque: {fecha_ini_str} a {fecha_fin_str}...")

        # Pausa de 2 segundos para cumplir con los límites de velocidad de la API de AEMET
        print("Pausa de 2 segundos...")
        time.sleep(2.0)

        # 1. EXTRACCIÓN
        datos_json = obtener_valores_climaticos_todas(fecha_ini_str, fecha_fin_str)

        # 2. TRANSFORMACIÓN
        if datos_json:
            df_lote = limpiar_y_cargar_datos(datos_json)
            if not df_lote.empty:
                print(f"Ok, bloque descargado. Registros nuevos: {len(df_lote)}")
                
                # 3. CARGA INCREMENTAL: Separamos el lote por años e integramos
                for anio in df_lote["fecha"].dt.year.unique():
                    df_lote_anio = df_lote[df_lote["fecha"].dt.year == anio].copy()
                    integrar_y_guardar_datos(df_lote_anio, anio)
            else:
                print("El lote descargado no tiene registros válidos tras la transformación.")
        else:
            print(f"Error o vacío al descargar bloque de {fecha_ini_str} a {fecha_fin_str}")

        dias_procesados += dias_lote
        fecha_actual = fecha_ini_lote - timedelta(days=1)
        gc.collect()

    print("\n¡Proceso de descarga e integración completado con éxito!")

# Si se ejecuta este fichero directamente, corre el ETL
if __name__ == '__main__':
    ejecutar_etl()
