import subprocess
import time
import sys
import os
import urllib.request

print("==============================================")
print("Lanzador AEMET: Solo Streamlit")
print("==============================================")

print("Limpiando procesos (por si había un servidor anterior corriendo)...")
os.system("pkill -f 'streamlit run app_unificada.py' || true")
time.sleep(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app_path = os.path.join(BASE_DIR, "app_unificada.py")

print("\n1. Iniciando la Web (Streamlit) en puerto 8501...")
proceso_web = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", app_path, "--server.port", "8501", "--server.headless", "true"],
    cwd=BASE_DIR
)

# Intentamos obtener la IP pública de la instancia EC2
ip_publica = "18.198.208.67"
try:
    req = urllib.request.Request("http://169.254.169.254/latest/meta-data/public-ipv4", method="GET")
    with urllib.request.urlopen(req, timeout=2) as response:
        ip_publica = response.read().decode('utf-8')
except Exception:
    pass

print("\n¡Todo listo!")
print(f"Streamlit (Panel Web): http://{ip_publica}:8501")
print("(Recuerda que la API FastAPI debe estar iniciada previamente con run_api.py)")
print("\nPresiona Ctrl+C para detener el servidor web.")

try:
    while True:
        time.sleep(10)
except KeyboardInterrupt:
    print("\nDeteniendo servidor Streamlit...")
    proceso_web.terminate()
    proceso_web.wait()
    print("¡Servidor detenido correctamente!")
