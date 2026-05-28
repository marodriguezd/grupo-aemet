# Proyecto AEMET (grupo-aemet)

Repositorio colaborativo para obtener, procesar y analizar datos climatológicos públicos a partir de la API OpenData de la AEMET (Agencia Estatal de Meteorología).

## Estructura del Repositorio

El desarrollo se realiza de manera independiente por cada miembro del equipo en sus respectivas carpetas:

* **`Carmen/`**, **`Miguel/`**, **`Tamara/`**, **`Truji/`**: Carpetas de trabajo individual.
* **`General/`**: Espacio común donde se centralizan las dependencias compartidas y utilidades globales.

---

## Configuración del Entorno Virtual (Python)

Cada integrante puede inicializar su propio entorno virtual (`venv`) de forma local dentro de su carpeta ejecutando los siguientes comandos:

### 1. Inicializar el entorno virtual
Navega a tu carpeta de desarrollo (por ejemplo, `Miguel/`) y ejecuta:

```bash
python -m venv .venv
```

### 2. Activar el entorno
* **Linux/macOS:**
  ```bash
  source .venv/bin/activate
  ```
* **Windows (Git Bash):**
  ```bash
  source .venv/Scripts/activate
  ```
* **Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```

### 3. Instalar las dependencias
Instala los paquetes necesarios definidos en el archivo compartido de la carpeta `General/`:

```bash
pip install --upgrade pip
pip install -r ../General/requirements.txt
```

---

## Requisito de API Key

Para interactuar con los endpoints de la AEMET, cada miembro debe registrarse en el portal [AEMET OpenData](https://opendata.aemet.es/centrodedescargas/inicio) y generar un API Token. 

Crea un archivo `.env` en tu directorio de desarrollo local (el cual está configurado en `.gitignore` para no ser subido):

```env
AEMET_API_KEY=tu_clave_aemet_aqui
```
