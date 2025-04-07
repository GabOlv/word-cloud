import threading
from word_cloud.utils.csv_sync import update_csv

from sqlmodel import Session, select
from word_cloud.data.model import Word, get_sql_engine

engine = get_sql_engine()

with Session(engine) as session:
    words = session.exec(select(Word)).all()
    print(f"Total de palavras no banco: {len(words)}")
    for w in words:
        print(f"{w.id} - {w.text}")

if __name__ == "__main__":
    t = threading.Thread(target=update_csv, daemon=True)
    t.start()
