# -*- coding: utf-8 -*-
import os
import time
import requests
from dotenv import load_dotenv
from pathlib import Path

# Buscamos el archivo .env para la API KEY de AEMET en la carpeta padre
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / '.env'

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print("Archivo .env cargado con éxito en extracción.")
else:
    load_dotenv()
    print("No se encontró el .env en la ruta esperada, buscando en el entorno general.")

# Obtenemos la API Key
API_KEY = os.getenv('AEMET_API_KEY')
if not API_KEY:
    raise RuntimeError('No se encontró AEMET_API_KEY en las variables de entorno del archivo .env.')

# Preparamos las cabeceras para la petición a la API
headers = {
    'cache-control': "no-cache",
    'api_key': API_KEY,
    'accept': "application/json"
}

# Función para traer el listado de todas las estaciones climatológicas
def obtener_inventario_estaciones():
    url_base = "https://opendata.aemet.es/opendata/api/valores/climatologicos/inventarioestaciones/todasestaciones"
    print("Pidiendo el inventario a la API:", url_base)
    try:
        response = requests.get(url_base, headers=headers, timeout=30)
        if response.status_code == 200:
            meta_datos = response.json()
            print(f"Respuesta API: {meta_datos.get('descripcion')} (Estado: {meta_datos.get('estado')})")
            
            if meta_datos.get('estado') == 200:
                url_datos = meta_datos.get('datos')
                print("Tenemos enlace temporal, descargando los datos reales...")
                
                # Segunda llamada para bajar el JSON con los datos de las estaciones
                datos_response = requests.get(url_datos, timeout=30)
                if datos_response.status_code == 200:
                    return datos_response.json()
                else:
                    print("Error al descargar datos finales, código:", datos_response.status_code)
            else:
                print("Error en AEMET:", meta_datos.get('descripcion'))
        else:
            print("Error de red en la primera llamada:", response.status_code)
    except Exception as e:
        print("Ha ocurrido una excepción al traer estaciones:", e)
    return None

# Petición para una sola estación (útil para hacer pruebas)
def obtener_valores_climaticos(fecha_ini_utc, fecha_fin_utc, idema):
    url_base = f"https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos/fechaini/{fecha_ini_utc}/fechafin/{fecha_fin_utc}/estacion/{idema}"
    try:
        response = requests.get(url_base, headers=headers, timeout=30)
        if response.status_code == 200:
            meta_datos = response.json()
            if meta_datos.get('estado') == 200:
                url_final = meta_datos.get('datos')
                datos_response = requests.get(url_final, timeout=30)
                if datos_response.status_code == 200:
                    return datos_response.json()
                else:
                    print("Error descargando los datos climatológicos de la estación:", datos_response.status_code)
            else:
                return None
        else:
            print("Error de red al consultar estación:", response.status_code)
    except Exception as e:
        print("Excepción al consultar clima de la estación:", e)
    return None

# Petición para todas las estaciones con reintentos y esperas (backoff exponencial) si falla la API
def obtener_valores_climaticos_todas(fecha_ini_utc, fecha_fin_utc, max_retries=15, base_delay=5.0):
    url_base = f"https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos/fechaini/{fecha_ini_utc}/fechafin/{fecha_fin_utc}/todasestaciones"
    delay = base_delay
    for intento in range(max_retries):
        try:
            response = requests.get(url_base, headers=headers, timeout=30)
            
            # Si no tenemos permiso o no existe el endpoint, paramos directamente
            if response.status_code in [401, 403, 404]:
                print(f"Error grave {response.status_code}, no se puede reintentar.")
                return None
                
            if response.status_code == 200:
                meta_datos = response.json()
                estado = meta_datos.get('estado')
                
                if estado == 200:
                    url_final = meta_datos.get('datos')
                    datos_response = requests.get(url_final, timeout=30)
                    if datos_response.status_code == 200:
                        return datos_response.json()
                    elif datos_response.status_code in [401, 403, 404]:
                        print(f"Error grave en datos {datos_response.status_code}, no reintentamos.")
                        return None
                    else:
                        print(f"Intento {intento+1} fallido al descargar datos: {datos_response.status_code}")
                elif estado in [401, 403, 404]:
                    print(f"Error API: Estado {estado}: {meta_datos.get('descripcion')}. No se reintentará.")
                    return None
                elif estado == 429:
                    print(f"Intento {intento+1}: La API dice Estado 429 (Límite superado).")
                else:
                    print(f"Intento {intento+1}: API devolvió Estado {estado}: {meta_datos.get('descripcion')}")
            elif response.status_code == 429:
                print(f"Intento {intento+1}: HTTP 429 (Muchas peticiones).")
            else:
                print(f"Intento {intento+1}: Código de red {response.status_code}")
                
        except Exception as e:
            print(f"Intento {intento+1}: Error de red/conexión: {e}")
            
        if intento < max_retries - 1:
            print(f"Esperando {delay} segundos antes de reintentar...")
            time.sleep(delay)
            delay *= 2.0
            
    print(f"No se pudo descargar el bloque tras {max_retries} intentos.")
    return None
