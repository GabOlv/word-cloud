import streamlit as st
import pandas as pd
import os
import sys
import matplotlib.pyplot as plt
import numpy as np
import random
from PIL import Image, ImageOps
from wordcloud import WordCloud
from spellchecker import SpellChecker
import unicodedata
import re
import json
import io


# --- Asset Path Function ---
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = os.path.dirname(os.path.abspath(__file__))
    except Exception:
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            # Use MEIPASS path if frozen and __file__ is not reliable
            base_path = (
                os.path.dirname(sys.executable)
                if hasattr(sys, "executable")
                else sys._MEIPASS
            )  # Fallback
            # Adjust base path if assets are relative to script location within MEIPASS
            expected_script_dir = os.path.join(base_path, "nuvem", "pages")
            if os.path.exists(
                expected_script_dir
            ):  # Check if our expected structure exists
                base_path = expected_script_dir
        else:
            base_path = os.path.abspath(".")

    asset_dir = os.path.join(base_path, "assets")
    final_path = os.path.join(asset_dir, relative_path)
    # print(f"DEBUG: Resource Path calculated for '{relative_path}': {final_path}") # Uncomment for debug
    return final_path


# --- END Asset Path Function ---


# --- Streamlit Page Configuration ---
st.set_page_config(page_title="Nuvem de Palavras", layout="centered", page_icon="☁️")


# --- Load Assets with Error Handling ---
# @st.cache_resource # Cache resource loading
def carregar_palavras_tecnicas():
    palavras = set()
    try:
        path = resource_path("words.txt")
        if not os.path.exists(path):
            st.error(f"Arquivo de palavras tecnicas nao encontrado em: {path}")
        else:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                # Safer alternative to eval if format is simple list/set string
                try:
                    palavras = set(
                        json.loads(content.replace("'", '"'))
                    )  # Try JSON first
                except json.JSONDecodeError:
                    try:
                        palavras = set(eval(content))  # Fallback to eval if necessary
                    except Exception as eval_e:
                        st.error(
                            f"Erro critico ao processar 'words.txt' com eval: {eval_e}"
                        )

    except FileNotFoundError:
        st.error(f"Arquivo de palavras tecnicas 'words.txt' nao encontrado.")
    except Exception as e:
        st.error(f"Erro inesperado ao carregar palavras tecnicas (words.txt): {e}")
    return palavras


# @st.cache_resource # Cache resource loading
def carregar_excecoes_singular():
    excecoes = {}
    try:
        path = resource_path("excecoes_singular.json")
        if not os.path.exists(path):
            st.error(f"Arquivo de excecoes nao encontrado em: {path}")
        else:
            with open(path, "r", encoding="utf-8") as f:
                excecoes = json.load(f)
    except FileNotFoundError:
        st.error(
            f"Arquivo de excecoes 'excecoes_singular.json' nao encontrado."
        )  # Specific error
    except json.JSONDecodeError as json_e:
        st.error(f"Erro ao decodificar JSON em 'excecoes_singular.json': {json_e}")
    except Exception as e:
        st.error(f"Erro inesperado ao carregar excecoes (excecoes_singular.json): {e}")
    return excecoes


# --- Load Data --- Can be upgraded and have more items added
PALAVRAS_TECNICAS = carregar_palavras_tecnicas()
EXCECOES_SINGULAR = carregar_excecoes_singular()


# --- Text Processing Functions ---
def normalizar_palavra(palavra):
    palavra = str(palavra).lower()
    palavra = "".join(
        c
        for c in unicodedata.normalize("NFD", palavra)
        if unicodedata.category(c) != "Mn"
    )
    palavra = re.sub(r"[^a-zA-Z\s]", "", palavra)
    return palavra.strip()


# handle plural to singular expressions
def singularizar(palavra):
    if not isinstance(palavra, str) or not palavra:
        return palavra
    palavra_lower = palavra
    if palavra_lower in EXCECOES_SINGULAR:
        return EXCECOES_SINGULAR[palavra_lower]
    if palavra_lower.endswith(("ões", "ães", "ãos")):
        return palavra_lower[:-3] + "ão"
    if palavra_lower.endswith("ns"):
        return palavra_lower[:-2] + "m"
    if palavra_lower.endswith("eis"):
        return palavra_lower[:-3] + "el"
    if palavra_lower.endswith("ais"):
        return palavra_lower[:-2] + "l"
    if palavra_lower.endswith("óis"):
        return palavra_lower[:-2] + "l"
    if palavra_lower.endswith("uis"):
        return palavra_lower[:-2] + "l"
    if palavra_lower.endswith("res") and len(palavra_lower) > 3:
        return palavra_lower[:-2]
    if palavra_lower.endswith("zes") and len(palavra_lower) > 3:
        return palavra_lower[:-2]
    if palavra_lower.endswith("s") and len(palavra_lower) > 1:
        return palavra_lower[:-1]
    return palavra_lower


def capitalizar(palavra):
    return " ".join(w.capitalize() for w in palavra.split())


# --- CSV Processing ---
@st.cache_data  # Cache the processing result
def processar_csv(file_content):
    df = None
    spell = None
    try:
        df = pd.read_csv(io.BytesIO(file_content))
    except Exception as e:
        st.error(f"Erro ao ler o arquivo CSV: {e}")
        return None, None

    if df.shape[1] < 2:
        st.error("CSV invalido: precisa ter pelo menos duas colunas.")
        return None, None

    try:
        spell = SpellChecker(language="pt")
        if PALAVRAS_TECNICAS:
            spell.word_frequency.load_words(PALAVRAS_TECNICAS)
    except Exception as e:
        # *** Use st.warning for non-critical errors like spellchecker init failure ***
        st.warning(
            f"Falha ao inicializar o corretor ortografico: {e}. Continuara sem correcao."
        )
        spell = None

    palavras_corrigidas = []
    segunda_coluna = df.iloc[:, 1]

    for texto in segunda_coluna:
        texto_str = str(texto)
        palavras_originais = texto_str.split()
        palavras_processadas_texto = []
        for palavra_original in palavras_originais:
            normalizada = normalizar_palavra(palavra_original)
            if not normalizada:
                continue
            corrigida = normalizada
            if normalizada not in PALAVRAS_TECNICAS and spell:
                correcao = spell.correction(normalizada)
                corrigida = correcao if correcao else normalizada
            singular = singularizar(corrigida)
            palavras_processadas_texto.append(singular)
        final = capitalizar(" ".join(p for p in palavras_processadas_texto if p))
        palavras_corrigidas.append(final)

    palavras_validas = [p for p in palavras_corrigidas if p]
    if not palavras_validas:
        st.warning("Nenhuma palavra valida encontrada apos o processamento.")
        return {}, None

    frequencias = pd.Series(palavras_validas).value_counts()
    freq_df = pd.DataFrame(
        {"Palavra": frequencias.index, "Frequencia": frequencias.values}
    )
    return frequencias.to_dict(), freq_df


# --- Streamlit App Logic ---
st.title("☁️ Nuvem de Palavras")

# Initialize session state
if "frequencias" not in st.session_state:
    st.session_state.frequencias = None
if "freq_df" not in st.session_state:
    st.session_state.freq_df = None
if "error_message" not in st.session_state:
    st.session_state.error_message = None


# --- Conditional UI Rendering ---
if st.session_state.frequencias is None and st.session_state.error_message is None:
    # --- Uploader View ---
    st.markdown(
        "Faça o upload de um arquivo CSV (palavras na segunda coluna) para gerar a nuvem."
    )
    uploaded_file = st.file_uploader(
        "📂 Selecione o arquivo CSV", type=["csv"], key="csv_uploader"
    )

    if uploaded_file is not None:
        with st.spinner("Processando CSV e gerando nuvem..."):
            file_content = uploaded_file.getvalue()
            frequencias_calculadas, freq_df_calculado = processar_csv(file_content)

            if frequencias_calculadas is not None:
                st.session_state.frequencias = frequencias_calculadas
                st.session_state.freq_df = freq_df_calculado
                st.session_state.error_message = None
                st.rerun()
            else:
                # Error occurred during processing (should be shown by processar_csv)
                st.session_state.error_message = (
                    "Falha ao processar CSV. Verifique o arquivo ou os erros acima."
                )
                st.session_state.frequencias = None
                st.session_state.freq_df = None
                st.rerun()
else:
    # --- Results / Error View ---
    if st.session_state.error_message:
        st.error(st.session_state.error_message)
        if st.button("Tentar novamente com outro arquivo"):
            st.session_state.frequencias = None
            st.session_state.freq_df = None
            st.session_state.error_message = None
            st.experimental_rerun()  # Use newer rerun if available

    elif st.session_state.frequencias:
        # --- Display Word Cloud ---
        frequencias = st.session_state.frequencias
        st.subheader("Nuvem Gerada")
        try:
            font_path = resource_path("Poppins-Light.ttf")
            mask_path = resource_path("nuvem.png")

            if not os.path.exists(font_path):
                st.error(f"Arquivo da fonte nao encontrado: {font_path}")
            elif not os.path.exists(mask_path):
                st.error(f"Arquivo da mascara nao encontrado: {mask_path}")
            else:
                nuvem_image = Image.open(mask_path)
                nuvem_mask = np.array(nuvem_image.convert("L"))
                nuvem_mask = np.where(nuvem_mask > 128, 255, 0).astype(np.uint8)
                cores_palavras = ["#27AEE2", "#E94F64", "#B685F4", "#55D17C", "#FFD166"]

                def color_func(
                    word, font_size, position, orientation, random_state=None, **kwargs
                ):
                    return random.choice(cores_palavras)

                wordcloud = WordCloud(
                    width=1000,
                    height=800,
                    background_color="white",
                    prefer_horizontal=0.9,
                    max_words=300,
                    scale=2,
                    font_path=font_path,
                    relative_scaling=0.3,
                    margin=10,
                    mask=nuvem_mask,
                    random_state=42,
                    collocations=False,
                    normalize_plurals=False,
                    min_font_size=10,
                    color_func=color_func,
                ).generate_from_frequencies(frequencias)
                fig, ax = plt.subplots(figsize=(12, 8))
                ax.imshow(wordcloud, interpolation="bilinear")
                ax.axis("off")
                fig.patch.set_alpha(0)
                st.pyplot(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Erro inesperado ao gerar/exibir a nuvem de palavras: {e}")
            st.exception(e)

        # --- Download Frequencies Button ---
        if st.session_state.freq_df is not None:
            st.subheader("Frequência das Palavras")
            csv_string = st.session_state.freq_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📊 Baixar Frequências (.csv)",
                data=csv_string,
                file_name="frequencia_palavras.csv",
                mime="text/csv",
                key="download_csv_button",
            )
