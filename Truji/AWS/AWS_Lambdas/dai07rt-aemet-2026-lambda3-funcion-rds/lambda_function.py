import json
import boto3
import os
from io import StringIO
import pandas as pd
from funtion_insertar_rds import insertar_rds_dai07rt_proyecto_aemet_2026

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    Orquestador AWS Lambda.
    1. Recibe el evento de subida de un CSV limpio a S3 (Bucket [dai07rt-proyecto-aemet-2026-limpio]).
    2. Mapeamos CSV a formato dataframe
    3. Invoca la función externa de inserccion a RDS.
    4. Copiar el archivo CSV limpio de (entradas/csv_limpio/ a entradas/csv_procesados/) en el mismo (Bucket [dai07rt-proyecto-aemet-2026-limpio])
    5. Borrar el archivo CSV limpio de la ruta (entradas/csv_limpio/) del bucket_origen  
    """
    try:

        # 1. Extraer detalles del objeto S3 origen
        bucket_origen = event['Records'][0]['s3']['bucket']['name']
        key_origen = event['Records'][0]['s3']['object']['key']
        
        print(f"====================================================================================")
        print(f"===>  Bucket_origen [{bucket_origen}]")
        print(f"===>  Key_origen    [{key_origen}]")
        print(f"====================================================================================")
        print(f"")
        
        # 2. Mapeamos CSV a formato dataframe       
        response = s3_client.get_object(Bucket=bucket_origen, Key=key_origen)
        data = response["Body"].read().decode("utf-8")

        # Convertir a DataFrame y creamos un buffer 
        buffer = StringIO(data)
        df = pd.read_csv(buffer)        

        # Reemplazar los valores NaN de Pandas por None para que en BD se inserten como NULL
        df = df.astype(object).where(pd.notnull(df), None)        
        
        # 3. Invocar la funcion externa de inserccion a RDS
        print(f"")
        print(f"======================================================================================================================================")
        print(f"Invocar la funcion externa de inserccion a RDS [ insertar_rds_dai07rt_proyecto_aemet_2026(df) ]")
        print(f"======================================================================================================================================")
        print(f"")

        insertar_rds_dai07rt_proyecto_aemet_2026(df)
        
        # 4. Copiar el archivo de (entradas/json/ a entradas/json_procesados/) en el mismo bucket_origen 

        #  Definir la nueva clave de procesados (mover de entradas/csv_limpio/ a entradas/csv_procesados/) en el mismo bucket_origen
        key_procesados = key_origen.replace("entradas/csv_limpio/", "entradas/csv_procesados/") 

        s3_client.copy_object(
            Bucket     = bucket_origen,
            CopySource = {'Bucket': bucket_origen, 'Key': key_origen},
            Key        = key_procesados
        )

        print(f"")
        print(f"======================================================================================================================================")
        print(f"Archivo original movido a una nueva ruta: {key_procesados} en el bucket {bucket_origen}")
        print(f"======================================================================================================================================")
        print(f"")


        # 5. Borrar el archivo csv limpio original del (Bucket [dai07rt-proyecto-aemet-2026-limpio])
        s3_client.delete_object(
            Bucket = bucket_origen,
            Key    = key_origen
        )

        print(f"")
        print(f"============================================================================================================")
        print(f"Archivo sucio original eliminado de {bucket_origen}: {key_origen}")
        print(f"============================================================================================================")
        print(f"")
       
        return {
             'statusCode': 200,
             'body': json.dumps(f'Éxito: Archivo procesado y trasladado al bucket {bucket_origen} como {key_procesados}')
         }
        
    except Exception as e:
        print(f"Error critico en ejecucion carga de CSV a RDS: {str(e)}")
        raise e
