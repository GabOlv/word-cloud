import streamlit as st
from wordcloud import WordCloud
import matplotlib.pyplot as plt

st.title("Nuvem de Palavras")

try:
    with open("palavras.txt", "r") as f:
        texto = f.read()
except FileNotFoundError:
    texto = ""

if texto:
    wc = WordCloud(width=800, height=400).generate(texto)
    fig, ax = plt.subplots()
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig)
else:
    st.info("Nenhuma palavra ainda.")
