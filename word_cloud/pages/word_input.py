import streamlit as st

st.title("Enviar Palavras")

palavra = st.text_input("Digite uma palavra:")

if st.button("Enviar"):
    with open("palavras.txt", "a") as f:
        f.write(palavra + "\n")
    st.success("Palavra salva!")
