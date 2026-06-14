# Resumen del estado del ETL AEMET

## Contexto
El proyecto AEMET se ha desarrollado en dos frentes paralelos:
- **Miguel/Truji** → extracción, transformación y guardado en CSV (local).
- **Tamara** → carga de esos CSVs a PostgreSQL local y pruebas con la API.

Ambos equipos han hecho un gran trabajo, pero al ir por separado han surgido **desconexiones** que ahora toca resolver para llegar a la meta final: un pipeline serverless en AWS (Lambda + S3 + RDS).

## ✅ Lo que ya funciona bien
- `extracción.py` se conecta a la API AEMET con control de errores.
- `transformación.py` limpia los datos crudos (comas→puntos, `Ip`→0.0, etc.).
- `carga.py` descarga datos por años y evita duplicados con `(fecha, indicativo)`.
- Tamara ha creado el esquema de tablas (`estaciones`, `datos_climaticos`) y la carga a PostgreSQL funciona.
- La conversión de coordenadas AEMET a decimal también está resuelta.

## ❌ Lo que está mal y debe corregirse
1. **Fechas futuras** – `carga.py` usa `fecha_fin = datetime(2026,5,30)`. La API no devuelve datos de ese año.
2. **Pausa entre años** – El notebook original documentaba 60 segundos, pero `carga.py` solo espera 2 segundos entre lotes. Riesgo de bloqueo por rate limiting.
3. **API key hardcodeada** – En `Tamara/ETL .ipynb` aparece una clave visible. Debe ir en `.env`.
4. **Lógica duplicada** – `SQL _TABLAS.ipynb` reescribe la transformación que ya existe en `transformación.py`. Cualquier cambio futuro se olvidará en uno de los dos sitios.
5. **Código muerto** – Función `cargar_datos_climaticos_a_db()` definida pero nunca llamada.
6. **Sin conexión a AWS** – No hay handlers Lambda, ni S3, ni RDS real. Todo el flujo es local.
7. **Nomenclatura inconsistente** – Miguel usa `indicativo`, Tamara usa `id` en la BD. Si no se unifica, habrá conflictos.

## 🎯 Prioridades de acción

### Inmediato (esta semana)
- Cambiar fecha fin por `datetime.now()` en `carga.py`.
- Añadir `time.sleep(60)` entre años.
- Eliminar la API key hardcodeada y usar `.env`.
- Que `SQL _TABLAS.ipynb` importe `transformación.py` en lugar de reescribir la limpieza.
- Unificar nombre de columna: mantener `indicativo` en Python y mapear a `id` solo en el INSERT a BD.

### Próximo paso (siguiente semana)
- Crear `carga_postgres.py` (script que lee CSVs y los inserta en PostgreSQL).
- Crear `cargar_estaciones.py` (poblar tabla de estaciones desde el inventario).
- Preparar handlers Lambda para extracción diaria (salida a S3) y carga desde S3 a RDS.

### Meta final
Tener un pipeline automático que cada día descargue los datos de AEMET, los transforme, los suba a S3 y los cargue en RDS, todo con Lambdas y EventBridge.

**Resumen:** Los bloques de construcción están hechos, solo falta unirlos y envolverlos para AWS. No empecemos de cero, conectemos lo que ya tenemos.