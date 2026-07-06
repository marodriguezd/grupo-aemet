# Estado Actual del Proyecto y Auditoría (AEMET Forecasting Pipeline)

Este documento resume el análisis del estado del proyecto comparando los requisitos iniciales definidos en [aemet.md](file:///home/marodriguezd/Github/grupo-aemet/aemet.md) con la implementación actual desarrollada principalmente en la carpeta [Miguel/](file:///home/marodriguezd/Github/grupo-aemet/Miguel/).

---

## 📊 Tabla Comparativa: Propuesta vs. Realidad

| Componente | Propuesta Teórica ([aemet.md](file:///home/marodriguezd/Github/grupo-aemet/aemet.md)) | Implementación Actual en [Miguel/](file:///home/marodriguezd/Github/grupo-aemet/Miguel/) | Estado |
| :--- | :--- | :--- | :--- |
| **Infraestructura Cloud** | Bucket S3 para crudos y PostgreSQL en AWS RDS. | Bucket S3 creado y Pipeline subido. BBDD RDS activa. Configuración de API Key en AWS. | **Completado (AWS)** |
| **Pipeline de Ingesta** | AWS Lambda con EventBridge (diario) y trigger de S3. | Funciones Python modulares desplegadas y corriendo en AWS Lambda mediante EventBridge. | **Completado (AWS)** |
| **Pipeline ETL & Limpieza** | Transformación en AWS Lambda de JSON a PostgreSQL. | Script ETL orquestado en AWS cargando la BBDD remota. | **Completado (AWS)** |
| **Almacenamiento Físico** | Base de Datos PostgreSQL. | Datos persistiéndose en PostgreSQL remoto (RDS). | **Completado (AWS)** |
| **Modelo de Forecasting** | Modelo decoder-only de Transformers para temperatura. | Sin empezar. | **Pendiente** |
| **Servicios API** | FastAPI desplegado en EC2 con endpoints `/ask` y `/forecast`. | Sin empezar. | **Pendiente** |
| **Interfaz de Usuario** | Dashboard en Streamlit para EDA interactivo y predicciones. | Sin empezar. | **Pendiente** |

---

## 🛠️ Detalles Técnicos de la Solución Implementada en `Miguel/`

La lógica desarrollada en [AEMET_Resumen editable.ipynb](file:///home/marodriguezd/Github/grupo-aemet/Miguel/AEMET_Resumen%20editable.ipynb) resuelve varios desafíos operacionales críticos con la API de AEMET OpenData:

1. **Estrategia de Descarga por Bloques (Evitar Caídas y Bloqueos)**:
   - Se segmenta la descarga masiva por años y en periodos de 15 días.
   - Aplica un **backoff exponencial** (`5s`, `10s`, `20s`, `40s`, etc.) al recibir códigos `HTTP 429` (Límite de peticiones) o sufrir pérdidas de conexión.
   - Timeout estricto de 30 segundos (`timeout=30`) para evitar bloqueos infinitos ante la inestabilidad del servidor de AEMET.

2. **Gestión Óptima de Memoria (RAM)**:
   - Procesamiento año a año de forma aislada.
   - Ordenación y persistencia inmediata en disco (`sheets/csv/` y `sheets/xlsx/`).
   - Uso de `gc.collect()` para liberar los DataFrames de la memoria antes de procesar el siguiente año.

3. **Pipeline ETL y Normalización de Datos**:
   - Reemplazo de comas por puntos en strings numéricos y conversión a `float32`.
   - Limpieza del parámetro de precipitación: conversión del indicador especial `"Ip"` (precipitación inapreciable) a `0.0` para posibilitar sumas matemáticas.
   - Manejo robusto de horas formateadas como texto anómalo (ej: `"Varias"`, vacío, `None`) mapeándolo a objetos `datetime.time`.

4. **Estabilidad en Jupyter Notebooks**:
   - Monkeypatch seguro sobre la clase `zipfile.ZipFile` para redefinir el deallocator (`_safe_zipfile_del`) marcando `_patched=True`, solucionando problemas de `RecursionError` al re-ejecutar celdas en el mismo kernel.

---

## 🚀 Próximas Fases Prioritarias

1. **Despliegue e Integración Streamlit (Fase 02 - Web)**:
   - Integrar definitivamente el endpoint `/ask` (LangChain + Gemini) en el Frontend.
   - Apuntar las rutas de Streamlit a la IP pública de la instancia AWS EC2.
   - Desplegar la aplicación en Streamlit Community Cloud o EC2 para acceso global.

2. **Modelado y FastAPI (Fase 02)**:
   - Iniciar el diseño y entrenamiento del modelo de forecasting.
   - Desarrollar la aplicación FastAPI localmente para envolver el modelo y la consulta de datos históricos.
