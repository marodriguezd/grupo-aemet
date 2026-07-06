import os
import subprocess
import sys
import time

# Dependencias necesarias para el proyecto de Tamara
DEPENDENCIAS = [
    "fastapi",
    "uvicorn",
    "streamlit",
    "pandas",
    "requests",
    "scikit-learn",
    "psycopg",
    "psycopg-binary", 
    "httpx",
    "matplotlib",
    "seaborn",
    "plotly"
]

def main():
    print("🚀 Iniciando automatización del entorno para la App de AEMET...")
    
    # 1. Crear el entorno virtual si no existe
    venv_dir = ".venv"
    if not os.path.exists(venv_dir):
        print("📦 Creando entorno virtual (.venv)...")
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
    else:
        print("✅ Entorno virtual ya existe.")

    # Rutas a los ejecutables dentro del venv (Linux)
    python_venv = os.path.join(venv_dir, "bin", "python")
    pip_venv = os.path.join(venv_dir, "bin", "pip")

    # 2. Instalar dependencias
    print("⬇️ Verificando e instalando dependencias (esto puede tardar unos segundos)...")
    subprocess.run([pip_venv, "install", "--upgrade", "pip"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([pip_venv, "install"] + DEPENDENCIAS, check=True)
    
    print("✅ Todas las dependencias están instaladas.")
    print("==================================================")
    
    # 3. Lanzar FastAPI (Uvicorn) y Streamlit
    proceso_api = None
    proceso_web = None
    
    try:
        print("🔥 Levantando la API (FastAPI) en el puerto 8000...")
        proceso_api = subprocess.Popen(
            [python_venv, "-m", "uvicorn", "AEMET:app", "--host", "127.0.0.1", "--port", "8000"]
        )
        
        # Esperamos un poco para asegurarnos de que la API está lista
        time.sleep(3)
        
        print("🌐 Levantando la interfaz web (Streamlit) en el puerto 8501...")
        proceso_web = subprocess.Popen(
            [python_venv, "-m", "streamlit", "run", "app_aemet.py", "--server.port", "8501"]
        )
        
        print("\n==================================================")
        print("✨ ¡TODO LISTO! ✨")
        print("🌍 Puedes acceder a tu aplicación en: http://localhost:8501")
        print("🛑 Para detener ambos servidores, pulsa CTRL+C en esta terminal.")
        print("==================================================\n")
        
        # Bucle infinito para mantener el script vivo
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo los servidores de forma segura...")
        if proceso_web:
            proceso_web.terminate()
        if proceso_api:
            proceso_api.terminate()
        print("👋 ¡Hasta pronto!")
        sys.exit(0)

if __name__ == "__main__":
    main()
