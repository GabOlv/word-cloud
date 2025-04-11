"This entrypoint can be used to open the program in development mode."

import threading
import webview
import time
import os
import sys

app_path = os.path.join(os.path.dirname(__file__), "pages", "nuvem.py")


def start_streamlit():
    os.system(f"{sys.executable} -m streamlit run {app_path} --server.headless true")


if __name__ == "__main__":
    # Start Streamlit
    threading.Thread(target=start_streamlit, daemon=True).start()

    # Aguarda o servidor iniciar
    time.sleep(5)

    # Abre o app no navegador embutido (webview)
    webview.create_window("Nuvem de Palavras", "http://localhost:8501")
    webview.start()
