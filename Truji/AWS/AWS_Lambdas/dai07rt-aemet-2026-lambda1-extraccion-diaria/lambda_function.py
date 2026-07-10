import json
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
import os
from funtion_obtener_valores_climaticos import obtener_valores_climaticos_todas 

def lambda_handler(event, context):
    """
    Orquestador AWS Lambda para descargar datos diarios climaticos de AEMET
    1. Calcula las fechas (hace 4 días hasta hace 3 dias).
    2. Invoca la funcion que llama a la API de AEMET con reintentos.
    3. Guarda el JSON resultante directamente en un bucket de S3.
    """


    fecha_inicio = datetime.now() - timedelta(days = 4)
    fecha_fin    = datetime.now() - timedelta(days = 3)
    
    print(f"=================================================")          
    print(f"===>   fecha_inicio [{fecha_inicio}]")    
    print(f"===>   fecha_fin    [{fecha_fin}]")    
    print(f"=================================================")          
    print(f"")


    fecha_inicio_utc = f"{fecha_inicio.strftime('%Y-%m-%d')}T00:00:00UTC"
    fecha_fin_utc    = f"{fecha_fin.strftime('%Y-%m-%d')}T00:00:00UTC"

    print(f"=================================================")          
    print(f"===>   fecha_inicio_utc [{fecha_inicio_utc}]")    
    print(f"===>   fecha_fin_utc    [{fecha_fin_utc}]")    
    print(f"=================================================")          
    print(f"")

    # Llamada a la API
    resultados = obtener_valores_climaticos_todas(fecha_inicio_utc, fecha_fin_utc)
    if resultados:
        BUCKET_NAME = os.environ.get('BUCKET_ORIGEN_S3')
        KEY_NAME = os.environ.get('KEY_ORIGEN_S3') 
        s3 = boto3.client('s3')
        nombre_archivo = f"{KEY_NAME}{fecha_inicio.strftime('%Y-%m-%d')}.json"
        try:
            # Convertimos el diccionario a JSON (string) y luego a bytes UTF-8 para S3
            json_string = json.dumps(resultados, ensure_ascii=False)
            json_bytes  = json_string.encode('utf-8')
            
            # Subida directa a S3
            s3.put_object(
                Bucket=BUCKET_NAME, 
                Key=nombre_archivo, 
                Body=json_bytes,
                ContentType='application/json'
            )

            print(f"===================================================================================================") 
            print(f"Archivo guardado exitosamente en S3: s3://{BUCKET_NAME}/{nombre_archivo}")
            print(f"===================================================================================================") 
            print(f"")
            
            # Asumiendo que 'resultados' es una lista, si es un dict, adapta esto
            total = len(resultados) if isinstance(resultados, list) else 1
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'mensaje': 'Datos obtenidos y guardados en S3 con éxito',
                    'archivo': nombre_archivo,
                    'total_registros': total
                })
            }
            
        except ClientError as e:
            print(f"Error al subir el archivo a S3: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Fallo al guardar en S3', 'detalle': str(e)})
            }
    else:
        print("No se obtuvieron resultados de la API.")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'No se pudieron obtener los datos de la API de AEMET'})
        }