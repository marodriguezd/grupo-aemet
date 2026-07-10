# Funcion para insertar (archivo funciones en lambda)

import os
import psycopg
import pandas as pd

def insertar_rds_dai07rt_proyecto_aemet_2026(df):

    DATABASE_URI = os.getenv("DATABASE_URI")
    
    print(f"===============================================================================================================")          
    print(f"===>   Database de Proyecto en RDS [{DATABASE_URI}]")    
    print(f"===============================================================================================================")          
    print(f"")
 
    # Definimos la consulta INSERT mapeando  la tabla datos_climaticos
    query = """INSERT INTO datos_climaticos ( fecha , indicativo , nombre , provincia , altitud , tmed , prec , tmin , horatmin , 
                                              tmax , horatmax , dir , velmedia , racha , horaracha , sol , presMax , horaPresMax ,
                                              presMin , horaPresMin , hrMedia , hrMax , horaHrMax , hrMin , horaHrMin )                
                                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT ( indicativo , fecha ) DO NOTHING;"""

    # Columnas en el orden exacto esperado por la consulta SQL
    columnas = [ 'fecha' , 'indicativo' , 'nombre' , 'provincia' , 'altitud' , 'tmed' , 'prec' , 'tmin' , 'horatmin' , 'tmax' , 'horatmax' ,
                 'dir', 'velmedia' , 'racha' , 'horaracha' , 'sol' , 'presMax' , 'horaPresMax' , 'presMin' , 'horaPresMin' , 'hrMedia' ,
                 'hrMax' , 'horaHrMax' , 'hrMin' , 'horaHrMin' ]
 

    # Conexion a la base de datos RDS
    with psycopg.connect(DATABASE_URI) as conn:
        with conn.cursor() as cursor:
        
            # Convertimos las filas a una lista de tuplas para la inserción
            registros = list(df.itertuples(index=False, name=None))

            
            # Ejecutamos la inserción en lote (bulk insert)
            cursor.executemany(query, registros)

            print(f"")
            print(f"======================================================================================================================================")
            print(f"   ¡Exito! Se han procesado e insertado {len(registros)} registros .")
            print(f"======================================================================================================================================")
            print(f"")