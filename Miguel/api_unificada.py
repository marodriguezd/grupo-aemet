# -*- coding: utf-8 -*-
"""
API unificada combinando los endpoints funcionales de Tamara (histórico y predicciones) 
y el endpoint NLP de Miguel (Gemini Text-to-SQL).
Totalmente compatible con el frontend Streamlit.
"""

import os
import sys
import pickle
import warnings
from datetime import date
from typing import List, Dict

import pandas as pd
import numpy as np
import psycopg
from fastapi import FastAPI, HTTPException, Query, Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Langchain / Gemini
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
warnings.filterwarnings('ignore', category=UserWarning)

# ---- CONFIGURACIÓN BASE DE DATOS ----
HOST = "database-dai07rt-proyecto-aemet-2026.cr828ecqk1a6.eu-central-1.rds.amazonaws.com"
PORT = "5432"
DBNAME = "postgres"
USER_DB = "aemet2026"
PASSWORD_DB = "mondongo-dai07rt-aemet-2026"
DSN = f"postgresql://{USER_DB}:{PASSWORD_DB}@{HOST}:{PORT}/{DBNAME}"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- CONFIGURACIÓN LLM (MIGUEL) ----
ESQUEMA_BD = """
-- Tabla 1: Catálogo Maestro de Estaciones (Catálogo de ubicaciones)
CREATE TABLE estaciones (
    indicativo VARCHAR(10) PRIMARY KEY,
    nombre VARCHAR(150),
    provincia VARCHAR(100),
    latitud FLOAT,
    longitud FLOAT,
    altitud INT,
    indsinop VARCHAR(10)
);

-- Tabla 2: Historial de Mediciones Diarias (Datos climáticos acumulados día a día)
CREATE TABLE datos_climaticos (
    fecha DATE,
    indicativo VARCHAR(10) REFERENCES estaciones(indicativo),
    nombre VARCHAR(150),
    provincia VARCHAR(255),
    altitud INT,
    tmed FLOAT,
    prec FLOAT,
    tmin FLOAT,
    horatmin TIME,
    tmax FLOAT,
    horatmax TIME,
    dir FLOAT,
    velmedia FLOAT,
    racha FLOAT,
    horaracha VARCHAR(15),
    sol FLOAT,
    presMax FLOAT,
    horaPresMax TIME,
    presMin FLOAT,
    horaPresMin TIME,
    hrMedia FLOAT,
    hrMax FLOAT,
    horaHrMax TIME,
    hrMin FLOAT,
    horaHrMin TIME,
    PRIMARY KEY (indicativo, fecha)
);
"""

class ConsultaSQLGenerada(BaseModel):
    """Estructura de datos que debe devolver el LLM obligatoriamente."""
    query_sql: str = Field(description="Consulta SQL SELECT válida para PostgreSQL. Debe utilizar únicamente las tablas y campos del esquema provisto, sin inventar nombres.")
    explicacion: str = Field(description="Explicación sencilla y en español de qué hace la consulta SQL y cómo responde a la pregunta original del usuario.")

api_key_gemini = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if api_key_gemini:
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0.0)
    llm_estructurado = llm.with_structured_output(ConsultaSQLGenerada)

    prompt_plantilla = ChatPromptTemplate.from_messages([
        ("system", """Eres un experto en bases de datos PostgreSQL de un equipo de analistas de datos.
    Tu tarea es recibir una pregunta del usuario en español y traducirla a una consulta SQL SELECT correcta.

    Utiliza únicamente el siguiente esquema DDL de la base de datos para construir la consulta SQL:
    ---------------------
    {esquema_bd}
    ---------------------

    Instrucciones críticas:
    1. Devuelve una consulta SQL válida que se pueda ejecutar directamente en PostgreSQL.
    2. No agregues comillas inclinadas (```sql) dentro del campo de la query en el JSON final.
    3. Si la pregunta requiere buscar por provincia, realiza búsquedas utilizando LIKE de forma insensible a mayúsculas/minúsculas (ej: ILIKE '%madrid%') para evitar fallos de escritura.
    4. Asegúrate de hacer JOINs correctos entre estaciones y datos_climaticos usando el campo 'indicativo' cuando sea necesario.
    5. Explicale al usuario el proceso de la query de manera amigable en español en el campo explicacion.
    """),
        ("human", "Pregunta del usuario: {pregunta_usuario}")
    ])
    cadena_text_to_sql = prompt_plantilla | llm_estructurado
else:
    cadena_text_to_sql = None
    print("ADVERTENCIA: No se detectó GEMINI_API_KEY en las variables de entorno. El endpoint NLP fallará.")


# ---- APLICACIÓN FASTAPI ----
app = FastAPI(title="AEMET Unificada", description="API unificada con los modelos de Tamara y el NLP de Miguel.", version="1.0.0")

class PreguntaRequest(BaseModel):
    pregunta: str

class InputFeatures(BaseModel):
    features: List[float]

@app.get("/")
def bienvenida():
    return {"mensaje": "Bienvenido a la API Unificada de AEMET, para ver la documentación de la API ingrese a /docs"}

@app.get("/estaciones/lista", tags=["estaciones"])
def lista_estaciones():
    """Devuelve la lista completa de estaciones disponibles."""
    try:
        with psycopg.connect(DSN) as conn:
            with conn.cursor() as cur:
                query = "SELECT DISTINCT indicativo, nombre, provincia FROM datos_climaticos WHERE indicativo IS NOT NULL ORDER BY nombre;"
                cur.execute(query)
                filas = cur.fetchall()
        return {"estaciones": [{"idema": f[0], "nombre": f[1], "provincia": f[2]} for f in filas]}
    except Exception as e:
        print(f"Error BD estaciones: {e}")
        raise HTTPException(status_code=500, detail="Error al cargar las estaciones")

# ---- LÓGICA DE CACHÉ DE MODELOS (TAMARA) ----
cache_modelos_max = {}
cache_modelos_min = {}

def obtener_modelo_max(idema: str):
    if idema in cache_modelos_max:
        return cache_modelos_max[idema]

    ruta_archivo = os.path.join(BASE_DIR, "modelos_max", f"modelo_{idema}_max.pkl")
    if not os.path.exists(ruta_archivo):
        ruta_archivo = os.path.join(BASE_DIR, "modelos_max", f"modelo_{idema.replace('/', '_')}_max.pkl")
        
    if not os.path.exists(ruta_archivo):
        return None

    try:
        with open(file=ruta_archivo, mode="rb") as file:
            modelo = pickle.load(file)
        cache_modelos_max[idema] = modelo
        return modelo
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cargar el archivo de modelo max: {str(e)}")

def obtener_modelo_min(idema: str):
    if idema in cache_modelos_min:
        return cache_modelos_min[idema]

    ruta_archivo = os.path.join(BASE_DIR, "modelos_min", f"modelo_{idema}_min.pkl")
    if not os.path.exists(ruta_archivo):
        ruta_archivo = os.path.join(BASE_DIR, "modelos_min", f"modelo_{idema.replace('/', '_')}_min.pkl")
        
    if not os.path.exists(ruta_archivo):
        return None

    try:
        with open(file=ruta_archivo, mode="rb") as file:
            modelo = pickle.load(file)
        cache_modelos_min[idema] = modelo
        return modelo
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cargar el archivo de modelo min: {str(e)}")


@app.post("/modelos_max/{idema}/predict", tags=["modelos_max"])
def prediccion_temp_max_endpoint(idema: str, input_data: InputFeatures):
    """Predicción de temperatura máxima usando el modelo de la estación (Tamara/Miguel)."""
    modelo = obtener_modelo_max(idema)
    if modelo is None:
        raise HTTPException(status_code=404, detail=f"No se encontró un modelo para la estación con IDEMA: {idema}")

    try:
        X = np.array([[input_data.features[0]]])
        try:
            prediccion_numpy = modelo.predict(X)
        except ValueError:
            # Si el modelo espera dataframe (ej. xgboost guardado con pandas)
            df_in = pd.DataFrame([{"tmed": input_data.features[0]}])
            prediccion_numpy = modelo.predict(df_in)

        prediccion = prediccion_numpy.tolist()
        
        return {
            "status": "success",
            "idema": idema,
            "mensaje": "Predicción de temperatura máxima obtenida correctamente",
            "prediccion": prediccion if isinstance(prediccion[0], list) else [prediccion]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno al ejecutar la predicción del modelo: {str(e)}")

@app.post("/modelos_min/{idema}/predict", tags=["modelos_min"])
def prediccion_temp_min_endpoint(idema: str, input_data: InputFeatures):
    """Predicción de temperatura mínima usando el modelo de la estación (Tamara/Miguel)."""
    modelo = obtener_modelo_min(idema)
    if modelo is None:
        raise HTTPException(status_code=404, detail=f"No se encontró un modelo para la estación con IDEMA: {idema}")

    try:
        X = np.array([[input_data.features[0]]])
        try:
            prediccion_numpy = modelo.predict(X)
        except ValueError:
            df_in = pd.DataFrame([{"tmed": input_data.features[0]}])
            prediccion_numpy = modelo.predict(df_in)

        prediccion = prediccion_numpy.tolist()
        
        return {
            "status": "success",
            "idema": idema,
            "mensaje": "Predicción de temperatura mínima obtenida correctamente",
            "prediccion": prediccion if isinstance(prediccion[0], list) else [prediccion]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno al ejecutar la predicción del modelo: {str(e)}")

@app.get("/historico/ultima_tmed", tags=["historico"])
def ultima_tmed(idema: str = Query(..., alias="id")):
    """Consulta la última tmed registrada para una estación."""
    try:
        with psycopg.connect(DSN) as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT fecha, tmed, nombre 
                    FROM datos_climaticos 
                    WHERE indicativo = %s AND tmed IS NOT NULL
                    ORDER BY fecha DESC
                    LIMIT 1;
                """
                cur.execute(query, (idema,))
                fila = cur.fetchone()
                
        if fila:
            return {"fecha": str(fila[0]), "tmed": float(fila[1]), "nombre": str(fila[2])}
        else:
            raise HTTPException(status_code=404, detail="No hay datos de tmed para esta estación")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en BD: {e}")
        raise HTTPException(status_code=500, detail="Error al conectar a la BD")

@app.get("/historico/obtener_historico", tags=["historico"])
def obtener_historico(
    estacion_id: str = Query(..., alias="id", description="El ID de la estación (idema)"),
    fecha_inicio: date = Query(..., alias="fecha_inicio", description="Fecha de inicio del rango (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., alias="fecha_fin", description="Fecha de fin del rango (YYYY-MM-DD)")
):
    """Devuelve el histórico de temperaturas filtrado por estación y rango de fechas."""
    if fecha_inicio > fecha_fin:
        raise HTTPException(status_code=400, detail="La fecha de inicio no puede ser posterior a la fecha de fin.")

    try:
        with psycopg.connect(DSN) as conn:
            with conn.cursor() as cursor:
                query = """
                    SELECT fecha, tmax, tmed, tmin 
                    FROM datos_climaticos 
                    WHERE indicativo = %s AND fecha >= %s AND fecha <= %s
                    ORDER BY fecha;
                """
                cursor.execute(query, (estacion_id, fecha_inicio, fecha_fin))
                data = cursor.fetchall()
        
        if not data:
            return {"registros": []}
            
        df_historico = pd.DataFrame(data=data, columns=["fecha", "tmax", "tmed", "tmin"])
        df_historico["fecha"] = pd.to_datetime(df_historico["fecha"]).dt.date.astype(str)
        # Convertir NaNs a None para evitar fallos de serialización JSON en FastAPI
        df_historico = df_historico.replace({np.nan: None})
        
        return {"registros": df_historico.to_dict(orient="records")}

    except Exception as e:
        print(f"Error en base de datos: {e}")
        raise HTTPException(status_code=500, detail="Error al conectar o consultar la base de datos.")


# ---- ENDPOINT DE NLP (MIGUEL) ----

@app.post("/ask", tags=["nlp"])
async def ask_endpoint(payload: PreguntaRequest):
    """
    Endpoint que recibe una pregunta, llama al LLM, ejecuta la query en RDS
    y devuelve el resultado formateado en JSON junto al SQL generado. (Miguel)
    """
    if not cadena_text_to_sql:
        raise HTTPException(status_code=500, detail="El endpoint NLP no está configurado (Falta GEMINI_API_KEY).")

    pregunta = payload.pregunta
    if not pregunta.strip():
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía.")
    
    # 1. Llamamos a la API de Gemini
    try:
        respuesta_llm = cadena_text_to_sql.invoke({
            "esquema_bd": ESQUEMA_BD,
            "pregunta_usuario": pregunta
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en LLM Gemini: {str(e)}")
    
    sql = respuesta_llm.query_sql
    explicacion = respuesta_llm.explicacion
    
    # 2. Ejecutamos en la BD de AWS
    try:
        with psycopg.connect(DSN) as conexion:
            df = pd.read_sql(sql, conexion)
            
            # Limpieza para JSON
            df = df.replace({np.nan: None})
            for col in df.select_dtypes(include=['datetime64', 'datetimetz']).columns:
                df[col] = df[col].astype(str)
                
            registros = df.to_dict(orient="records")
            
            return {
                "pregunta": pregunta,
                "sql_generado": sql,
                "explicacion": explicacion,
                "registros_encontrados": len(registros),
                "datos": registros
            }
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail={
                "error": f"Error de sintaxis o ejecución de la query: {str(e)}",
                "sql_intentado": sql,
                "explicacion_llm": explicacion
            }
        )

if __name__ == "__main__":
    import uvicorn
    print("Iniciando la API unificada AEMET en http://127.0.0.1:8000")
    uvicorn.run("api_unificada:app", host="127.0.0.1", port=8000, reload=True)
