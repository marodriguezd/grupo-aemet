# -*- coding: utf-8 -*-
"""
Script rápido para probar la conexión a la base de datos AWS RDS
usando las credenciales encontradas en el repo.
"""

import psycopg
import pandas as pd

# Credenciales hardcodeadas (¡lo que queríamos evitar, pero muy útil para pruebas rápidas!)
DSN = "postgresql://aemet2026:mondongo-dai07rt-aemet-2026@database-dai07rt-proyecto-aemet-2026.cr828ecqk1a6.eu-central-1.rds.amazonaws.com:5432/postgres"

def probar_conexion():
    print("Intentando conectar a AWS RDS...")
    try:
        # Abrimos conexión
        with psycopg.connect(DSN) as conn:
            print("✅ ¡Conexión exitosa a la base de datos AWS RDS!")
            
            # Lanzamos una query rápida de prueba para ver las tablas que hay
            query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public';
            """
            df = pd.read_sql(query, conn)
            
            print("\nTablas encontradas en la base de datos:")
            if not df.empty:
                display(df) if 'get_ipython' in globals() else print(df)
            else:
                print("No hay tablas todavía en el esquema public.")
                
    except Exception as e:
        print(f"❌ Error al conectar con AWS RDS: {e}")

if __name__ == '__main__':
    probar_conexion()
