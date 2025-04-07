import threading
import webview
import time
import os
import sys

try:
    from word_cloud.utils.csv_sync import update_csv
except ImportError or ModuleNotFoundError:
    from utils.csv_sync import update_csv

app_path = os.path.join(os.path.dirname(__file__), "app.py")


def start_streamlit():
    os.system(f"{sys.executable} -m streamlit run {app_path} --server.headless true")


if __name__ == "__main__":
    # Start the Streamlit app
    threading.Thread(target=start_streamlit, daemon=True).start()

    # Start the CSV sync thread
    threading.Thread(target=update_csv, daemon=True).start()

    # Wait server start
    time.sleep(5)

    # Run the webview
    webview.create_window("Nuvem de Palavras", "http://localhost:8501/word_cloud")
    webview.start()
