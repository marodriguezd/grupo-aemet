import json
import os

with open("App_Interactiva.ipynb", "r") as f:
    nb = json.load(f)

new_source = """import subprocess
import time
import sys
import os

print("Limpiando puertos (por si había un servidor anterior corriendo)...")
os.system("pkill -f uvicorn || true")
os.system("pkill -f streamlit || true")
time.sleep(1)

print("Iniciando la API (FastAPI)...")
# Guardamos los logs en un archivo para poder revisar posibles errores
api_log = open("api.log", "w")
proceso_api = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "api_aemet:app", "--host", "127.0.0.1", "--port", "8000"],
    stdout=api_log,
    stderr=subprocess.STDOUT
)

time.sleep(3)

print("Iniciando la Web (Streamlit)...")
web_log = open("web.log", "w")
proceso_web = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", "web_aemet.py", "--server.port", "8501"],
    stdout=web_log,
    stderr=subprocess.STDOUT
)

print("¡Todo listo! Accede a http://localhost:8501 en tu navegador.")
"""

# Format into lines for the cell source
lines = new_source.split("\n")
formatted_lines = [line + "\n" for line in lines[:-1]] + [lines[-1]]

# Buscamos la celda de ejecución
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        source = cell.get("source", [])
        if len(source) > 0 and source[0].startswith("import subprocess"):
            cell["source"] = formatted_lines
            break

with open("App_Interactiva.ipynb", "w") as f:
    json.dump(nb, f, indent=2)

print("Notebook actualizado con logs y limpieza de procesos.")
