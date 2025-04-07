# main.py
import threading
import webview
import time
import os
import sys

app_path = os.path.join(os.path.dirname(__file__), "app.py")


def start_streamlit():
    os.system(f"{sys.executable} -m streamlit run {app_path} --server.headless true")


# Iniciar o Streamlit numa thread separada
threading.Thread(target=start_streamlit, daemon=True).start()

# Espera o servidor iniciar (ajuste se necessário)
time.sleep(5)

# Abre a janela com o PyWebview apontando para o Streamlit
webview.create_window("Nuvem de Palavras", "http://localhost:8501/word_cloud")
webview.start()
