import subprocess
import time
import sys
import os
import urllib.request

print("==============================================")
print("Lanzador AEMET: Solo FastAPI (API Unificada)")
print("==============================================")

print("Limpiando puertos (por si había un servidor anterior corriendo)...")
os.system("pkill -f 'uvicorn api_unificada:app' || true")
time.sleep(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
api_log = open(os.path.join(BASE_DIR, "api.log"), "w")

print("\n1. Iniciando la API (FastAPI) en puerto 8000...")
# Bind a 0.0.0.0 para escuchar conexiones externas
proceso_api = subprocess.Popen(
    [".venv/bin/python", "-m", "uvicorn", "api_unificada:app", "--host", "0.0.0.0", "--port", "8000"],
    stdout=api_log,
    stderr=subprocess.STDOUT,
    cwd=BASE_DIR
)

time.sleep(3) # Damos tiempo a que levante la API

# Intentamos obtener la IP pública de la instancia EC2
ip_publica = "18.198.208.67" # Fallback por defecto según el script de conexión
try:
    req = urllib.request.Request("http://169.254.169.254/latest/meta-data/public-ipv4", method="GET")
    with urllib.request.urlopen(req, timeout=2) as response:
        ip_publica = response.read().decode('utf-8')
except Exception:
    pass

print("\n¡API Lista!")
print(f"La API está escuchando conexiones externas.")
print(f"👉 Documentación (Swagger UI): http://{ip_publica}:8000/docs")
print(f"👉 Endpoint principal: http://{ip_publica}:8000")
print("\nPresiona Ctrl+C para detener el servidor.")

try:
    while True:
        time.sleep(10)
except KeyboardInterrupt:
    print("\nDeteniendo el servidor API...")
    proceso_api.terminate()
    proceso_api.wait()
    print("¡Servidor detenido correctamente!")
