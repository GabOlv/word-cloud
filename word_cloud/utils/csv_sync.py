import os
import sys
import time
import pandas as pd
from sqlmodel import Session, select

try:
    from word_cloud.data.model import Word, get_sql_engine
except ImportError or ModuleNotFoundError:
    from data.model import Word, get_sql_engine

last_saved_id = 0


# .exe data dir
def get_data_dir():
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:  # Normal dev environment
        base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.abspath(data_dir)


def get_csv_path():
    return os.path.join(get_data_dir(), "palavras.csv")


def update_csv():
    global last_saved_id
    engine = get_sql_engine()
    csv_path = get_csv_path()

    while True:
        time.sleep(5)

        with Session(engine) as session:
            statement = select(Word).where(Word.id > last_saved_id)
            results = session.exec(statement).all()

            if results:
                new_data = [(word.id, word.text) for word in results]
                df_new = pd.DataFrame(new_data, columns=["id", "text"])

                if os.path.exists(csv_path):
                    df_old = pd.read_csv(csv_path)
                    df = pd.concat([df_old, df_new], ignore_index=True)
                    df.drop_duplicates(subset=["id"], inplace=True)
                else:
                    df = df_new

                df.to_csv(csv_path, index=False)
                last_saved_id = max(word.id for word in results)
