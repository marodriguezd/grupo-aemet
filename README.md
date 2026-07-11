# Proyecto AEMET (grupo-aemet)

Repositorio colaborativo para obtener, procesar y analizar datos climatológicos públicos a partir de la API OpenData de la AEMET (Agencia Estatal de Meteorología).

## Estructura del Repositorio

El desarrollo se realiza de manera independiente por cada miembro del equipo en sus respectivas carpetas:

* **`Carmen/`**, **`Tamara/`**: Carpetas de trabajo individual.
* **`Miguel/`**: Contiene la implementación del pipeline de ingesta (descarga masiva y robusta), procesamiento ETL, pruebas de NLP (`NLP.ipynb`) y scripts para el despliegue en EC2 (`AEMET_Despliegue_EC2.ipynb` y app unificada).
* **`Truji/`**: Contiene el desarrollo y pruebas de la arquitectura en AWS (`AEMET_AWS.ipynb`, dashboards y recursos AWS) y despliegues en local (`AEMET_Local.ipynb`).

---

## Guía de Configuración paso a paso (¡Para todo el mundo!)

Sigue estos sencillos pasos para tener tu entorno listo en menos de 2 minutos.

### Paso 1: Abre la terminal
Abre tu terminal favorita (Git Bash, PowerShell, Terminal de VS Code, etc.) y colócate dentro de **tu carpeta personal** de trabajo:
```bash
cd Nombre   # Cambia "Nombre" por tu nombre de carpeta correspondiente
```

### Paso 2: Crea tu Entorno Virtual
Crea un entorno aislado para no ensuciar la instalación global de Python en tu sistema:
```bash
python -m venv .venv
```

### Paso 3: Activa tu Entorno Virtual
Dependiendo de qué sistema uses, debes activarlo ejecutando **uno** de estos comandos:

* **En Windows (si usas Git Bash):**
  ```bash
  source .venv/Scripts/activate
  ```
* **En Windows (si usas PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
* **En Linux / macOS:**
  ```bash
  source .venv/bin/activate
  ```

*(Sabrás que está activado porque verás `(.venv)` al inicio de la línea en tu consola).*

### Paso 4: Instala las librerías necesarias
Con el entorno activado, actualiza el gestor de paquetes e instala de golpe todas las dependencias del proyecto usando el archivo `requirements.txt` que está en la raíz:

```bash
pip install --upgrade pip
pip install -r ../requirements.txt
```

---

## Configuración de la API Key (Obligatorio)

Para poder descargar datos de la AEMET necesitas una clave.

1. Consigue tu clave registrándote en: [AEMET OpenData](https://opendata.aemet.es/centrodedescargas/inicio).
2. Crea un archivo de texto llamado **`.env`** dentro de **tu carpeta personal** (por ejemplo, dentro de `Miguel/`).
3. Añade la siguiente línea dentro del archivo `.env`:
   ```env
   AEMET_API_KEY=pega_aqui_tu_clave_de_aemet
   ```

*Nota: No te preocupes por la seguridad; el archivo `.env` está configurado para no subirse a Git.*
