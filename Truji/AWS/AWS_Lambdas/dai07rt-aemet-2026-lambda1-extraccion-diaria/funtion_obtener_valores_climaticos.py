import os 
import requests
import json
import time
from time import sleep

# Es buena práctica obtener la API key de las variables de entorno de la Lambda
API_KEY = os.environ.get('AEMET_API_KEY')
headers = {
           'cache-control': "no-cache",
           'api_key': API_KEY,
           'accept': "application/json"    
          }


# Petición para todas las estaciones con reintentos y esperas (backoff) si falla la API
def obtener_valores_climaticos_todas(fecha_ini_utc, fecha_fin_utc, max_retries=15, base_delay=5.0):
    url_base = f"https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos/fechaini/{fecha_ini_utc}/fechafin/{fecha_fin_utc}/todasestaciones"
    delay = base_delay
    for intento in range(max_retries):
        try:
            response = requests.get(url_base, headers=headers, timeout=30)
            
            # Si no tenemos permiso o no existe el endpoint, paramos
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
