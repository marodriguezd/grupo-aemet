import subprocess
import time
import sys
import os

print("==============================================")
print("Lanzador AEMET: FastAPI + Streamlit")
print("==============================================")

print("Limpiando puertos (por si había un servidor anterior corriendo)...")
os.system("pkill -f 'uvicorn api_unificada:app' || true")
os.system("pkill -f 'streamlit run app_unificada.py' || true")
time.sleep(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
api_path = os.path.join(BASE_DIR, "api_unificada.py")
app_path = os.path.join(BASE_DIR, "app_unificada.py")

print("\n1. Iniciando la API (FastAPI) en puerto 8000...")
api_log = open(os.path.join(BASE_DIR, "api.log"), "w")
# Usamos uvicorn directamente pasándole la ruta del módulo (cwd en BASE_DIR)
proceso_api = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "api_unificada:app", "--host", "127.0.0.1", "--port", "8000"],
    stdout=api_log,
    stderr=subprocess.STDOUT,
    cwd=BASE_DIR
)

time.sleep(3) # Damos tiempo a que levante la API

print("2. Iniciando la Web (Streamlit) en puerto 8501...")
proceso_web = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", app_path, "--server.port", "8501", "--server.headless", "true"],
    cwd=BASE_DIR
)

print("\n¡Todo listo!")
print("FastAPI (Swagger UI): http://127.0.0.1:8000/docs")
print("Streamlit (Panel Web): http://127.0.0.1:8501")
print("\nPresiona Ctrl+C para detener ambos servidores.")

try:
    while True:
        time.sleep(10)
except KeyboardInterrupt:
    print("\nDeteniendo servidores...")
    proceso_api.terminate()
    proceso_web.terminate()
    proceso_api.wait()
    proceso_web.wait()
    print("¡Servidores detenidos correctamente!")
