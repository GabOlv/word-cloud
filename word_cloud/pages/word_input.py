import streamlit as st
from sqlmodel import Session

from word_cloud.data.model import Word, get_sql_engine


def save_word_db(word_text: str, engine=None):
    engine = get_sql_engine() if engine is None else engine
    with Session(engine) as session:
        word_obj = Word(text=word_text.strip().lower())
        session.add(word_obj)
        session.commit()


st.title("Enviar Palavras")

word = st.text_input("Digite uma palavra:")

try:
    if word:
        save_word_db(word)
        st.success(f"A palavra '{word}' foi salva com sucesso!")
except Exception as e:
    st.error(f"Erro ao salvar a palavra, tente novamente")
