# Proyecto AEMET ( grupo-aemet )

Breve repositorio para obtener y procesar datos públicos de la AEMET (Agencia Estatal de Meteorología).

**Requisitos**
- Python 3.8 o superior
- Git Bash, PowerShell o CMD en Windows

**Instalación — Entorno virtual (venv)**

Para instalar el entorno virtual, se debe ejecutar el siguiente comando en la terminal.

`Powershell`
```
C:\Users\03010496\AppData\Local\Microsoft\WindowsApps\python.exe -m venv .env
```
`Git Bash`
```bash
python -m venv env  
```
Luego, se activa el entorno virtual con el siguiente comando:
`Git Bash`
```
source .venv/Scripts/activate
```
hay que instalar las dependencias necesarias para el proyecto.

`Git Bash`
```
python -m pip install --upgrade pip
python -m pip install pandas
python -m pip install requests
python -m pip install python-dotenv
```
  
**API AEMET — acceso y uso básico**

Portal de datos: https://opendata.aemet.es/centrodedescargas/inicio

Pasos para obtener la API key:
1. Crear cuenta en el portal de AEMET.
2. Solicitar acceso a la API desde el panel de usuario.
3. Copiar la clave (token) que proporciona AEMET.
4. Guardar la clave en un archivo `.env` para su uso en el proyecto. El contenido del archivo `.env` debe ser el siguiente: `AEMET_API_KEY=tu_clave_aemet_aqui`
5. Mirar la documentación oficial de la API para conocer los endpoints disponibles y cómo realizar las solicitudes. en la siguienes URL: https://opendata.aemet.es/dist/index.html#/valores-climatologicos/Inventario%20de%20estaciones%20(valores%20climatol%C3%B3gicos)


Para el proyecto, se tiene que utilizar las siguientes API endpoints:

- Inventario de estaciones (maestro de estaciones):
 `/api/valores/climatologicos/inventarioestaciones/todasestaciones`
- Inventario de estaciones (valores climatológicos):
 `/api/valores/climatologicos/diarios/datos/fechaini/{fechaIniStr}/fechafin/{fechaFinStr}/estacion/{idema}`


