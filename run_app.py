import subprocess
import time
import sys
import os

def run_app():
    print("🚀 Démarrage de DataCommerce...")
    
    # 1. Start Flask (Port 5001)
    print("📦 Lancement du serveur backend Flask (Port 5001)...")
    flask_process = subprocess.Popen(
        [sys.executable, "app_flask.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Wait a bit for Flask to initialize
    time.sleep(3)
    
    # 2. Start Streamlit (Port 8501)
    print("📊 Lancement de la plateforme Analytics Streamlit (Port 8501)...")
    # Use 'python -m streamlit' to be and use the current environment
    streamlit_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "ap.py", "--server.port", "8501", "--server.headless", "true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    print("\n✅ Application DataCommerce prête !")
    print("👉 Landing Page : http://localhost:5001")
    print("👉 Analytics Direct : http://localhost:8501")
    print("\nPressez Ctrl+C pour arrêter les serveurs.\n")

    try:
        while True:
            # Safely check for outputs to console
            # Print outputs from Flask if available
            if flask_process and flask_process.stdout:
                line = flask_process.stdout.readline()
                if line:
                    print(f"[Flask] {line.strip()}")
            
            # Print outputs from Streamlit if available
            if streamlit_process and streamlit_process.stdout:
                line = streamlit_process.stdout.readline()
                if line:
                    print(f"[Streamlit] {line.strip()}")
                    
            # Check if any process terminated
            if flask_process.poll() is not None or streamlit_process.poll() is not None:
                break
                
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt des serveurs...")
    finally:
        if flask_process: flask_process.terminate()
        if streamlit_process: streamlit_process.terminate()
        print("👋 Au revoir !")

if __name__ == "__main__":
    run_app()
