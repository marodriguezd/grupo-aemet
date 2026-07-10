import json
import boto3
import os
from funtion_limpieza import limpiar_y_cargar_datos_fechas_todas_estaciones

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    Orquestador AWS Lambda.
    1. Recibe el evento de subida de un JSON sucio a S3 (Bucket Origen).
    2. Descarga el JSON sucio.
    3. Invoca la función externa de limpieza.
    4. Sube el CSV limpio al Bucket Destino (leído desde variable de entorno).
    5. Guardar archivo limpio en el BUCKET DE DESTINO.
    6. Copiar el archivo JSON sucio de (entradas/json/ a entradas/json_procesados/) en el mismo bucket_origen
    7. Borrar el archivo JSON sucio original del bucket_origen
    """
    try:
        # 1. Obtener la variable de entorno del bucket de destino
        bucket_destino = os.environ.get('BUCKET_DESTINO')
        if not bucket_destino:
           raise ValueError("La variable de entorno BUCKET_DESTINO no está configurada en la Lambda.")

        print(f"====================================================================================")          
        print(f"===>   Bucket_destino[{bucket_destino}]")    
        print(f"====================================================================================")          
        print(f"")
            
        # Extraer detalles del objeto S3 origen
        bucket_origen = event['Records'][0]['s3']['bucket']['name']
        key_origen = event['Records'][0]['s3']['object']['key']
        
        print(f"====================================================================================")
        print(f"===>  Bucket_origen [{bucket_origen}]")
        print(f"===>  Key_origen    [{key_origen}]")
        print(f"====================================================================================")
        print(f"")
        print(f"=============================================================================================================================")
        print(f"Iniciando procesamiento ETL para: {key_origen} en el bucket de origen: {bucket_origen}")
        print(f"Bucket de destino configurado: {bucket_destino}")
        print(f"=============================================================================================================================")
        
        # 2. Obtener objeto de S3
        response = s3_client.get_object(Bucket=bucket_origen, Key=key_origen)
        contenido_json = json.loads(response['Body'].read().decode('utf-8'))
        
        # 3. Ejecutar limpieza e imputación
        df_limpio = limpiar_y_cargar_datos_fechas_todas_estaciones(contenido_json)
        
        if df_limpio.empty:
           print("El JSON procesado no arrojó registros válidos. Operación omitida.")
           return {
                    'statusCode': 200,
                    'body': json.dumps('ETL completado: sin datos válidos procesables.')
                  }
            
        # 4. Serializar DataFrame limpio a cadena de texto CSV (sin índice para tabla limpia)
        csv_limpio_str = df_limpio.to_csv(index=False)
        
        # Definir la nueva clave de destino (mover de entradas/json/ a entradas/csv_limpio/ y renombrar extensión)
        key_destino = key_origen.replace("entradas/json/", "entradas/csv_limpio/").replace(".json", ".csv")
        
        # 5. Guardar archivo limpio en el BUCKET DE DESTINO
        s3_client.put_object(
            Bucket=bucket_destino,
            Key=key_destino,
            Body=csv_limpio_str,
            ContentType='text/csv'
        )

        print(f"")
        print(f"=============================================================================================================================")
        print(f"Archivo limpio subido a: {key_destino} en el bucket {bucket_destino}")
        print(f"=============================================================================================================================")
        print(f"")


        # 6. Copiar el archivo de (entradas/json/ a entradas/json_procesados/) en el mismo bucket_origen 

        # Definir la nueva clave de procesados (mover de entradas/json/ a entradas/json_procesados/) en el mismo bucket_origen
        key_procesados = key_origen.replace("entradas/json/", "entradas/json_procesados/") 

        s3_client.copy_object(
            Bucket     = bucket_origen,
            CopySource = {'Bucket': bucket_origen, 'Key': key_origen},
            Key        = key_procesados
        )

        print(f"")
        print(f"===============================================================================================================================")
        print(f"Archivo original movido a una nueva ruta: {key_procesados} en el bucket {bucket_origen}")
        print(f"================================================================================================================================")
        print(f"")


        # 7. Borrar el archivo sucio original del BUCKET DE ORIGEN
        s3_client.delete_object(
             Bucket=bucket_origen,
             Key=key_origen
         )

        print(f"")
        print(f"============================================================================================================")
        print(f"Archivo sucio original eliminado de {bucket_origen}: {key_origen}")
        print(f"============================================================================================================")
        print(f"")
       
        return {
             'statusCode': 200,
             'body': json.dumps(f'Éxito: Archivo procesado y trasladado al bucket {bucket_destino} como {key_destino}')
         }
        
    except Exception as e:
        print(f"Error crítico en ejecución ETL: {str(e)}")
        raise e
