from sqlmodel import Session, select
from word_cloud.data.model import Word, get_sql_engine


# Add a new word to the DB
def create_word(word_text: str, engine=None):
    engine = get_sql_engine() if engine is None else engine
    with Session(engine) as session:
        word_obj = Word(text=word_text)
        session.add(word_obj)
        session.commit()
        session.refresh(word_obj)
        return word_obj


# Fetch all words
def read_all_words(engine=None):
    engine = get_sql_engine() if engine is None else engine
    with Session(engine) as session:
        return session.exec(select(Word)).all()
