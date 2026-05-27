import streamlit as st
import pandas as pd
import os
import sys
import matplotlib.pyplot as plt
import numpy as np
import random
from PIL import Image
from wordcloud import WordCloud
from spellchecker import SpellChecker
import unicodedata
import re
import json
import io
from difflib import get_close_matches


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


# --- Text Processing Functions ---
def remover_acentos(texto):
    texto = str(texto).lower()
    return "".join(
        c
        for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


def normalizar_palavra(palavra):
    palavra = remover_acentos(palavra)
    palavra = re.sub(r"[^a-zA-Z0-9+#\s-]", "", palavra)
    palavra = re.sub(r"\s+", " ", palavra)
    return palavra.strip()


def capitalizar(palavra):
    palavras_minusculas = {"a", "as", "com", "da", "das", "de", "do", "dos", "e", "em", "o", "os"}
    partes = []
    for index, parte in enumerate(palavra.split()):
        if index > 0 and parte in palavras_minusculas:
            partes.append(parte)
        elif parte in {"ai", "api", "cpu", "db", "dns", "gpu", "hd", "ia", "ip", "lgpd", "ml", "pc", "pdf", "ram", "ssd", "ui", "url", "ux", "vpn"}:
            partes.append(parte.upper())
        else:
            partes.append(parte.capitalize())
    return " ".join(partes)


# --- Load Assets with Error Handling ---
# @st.cache_resource # Cache resource loading
def carregar_palavras_tecnicas():
    palavras = set()
    try:
        path = resource_path("words.txt")
        if not os.path.exists(path):
            st.warning(f"Arquivo de palavras tecnicas nao encontrado em: {path}")
            return palavras

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            palavras_raw = json.loads(content)
        except json.JSONDecodeError:
            # words.txt is currently a Python-like list with comments/trailing commas.
            # Extract quoted terms instead of using eval so a typo in the asset cannot execute code.
            palavras_raw = [
                match.group(1) or match.group(2)
                for match in re.finditer(r'"([^"]+)"|\'([^\']+)\'', content)
            ]

        for palavra in palavras_raw:
            normalizada = normalizar_palavra(palavra)
            if normalizada:
                palavras.add(normalizada)

    except FileNotFoundError:
        st.warning("Arquivo de palavras tecnicas 'words.txt' nao encontrado.")
    except Exception as e:
        st.warning(f"Erro inesperado ao carregar palavras tecnicas (words.txt): {e}")
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
                excecoes_raw = json.load(f)
                excecoes = {
                    normalizar_palavra(plural): normalizar_palavra(singular)
                    for plural, singular in excecoes_raw.items()
                    if normalizar_palavra(plural) and normalizar_palavra(singular)
                }
    except FileNotFoundError:
        st.error(
            f"Arquivo de excecoes 'excecoes_singular.json' nao encontrado."
        )  # Specific error
    except json.JSONDecodeError as json_e:
        st.error(f"Erro ao decodificar JSON em 'excecoes_singular.json': {json_e}")
    except Exception as e:
        st.error(f"Erro inesperado ao carregar excecoes (excecoes_singular.json): {e}")
    return excecoes


def carregar_lista_texto(relative_path):
    itens = set()
    path = resource_path(relative_path)
    if not os.path.exists(path):
        st.warning(f"Arquivo de lista nao encontrado: {path}")
        return itens

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                item = line.strip()
                if item and not item.startswith("#"):
                    itens.add(normalizar_palavra(item))
    except Exception as e:
        st.warning(f"Erro ao carregar lista '{relative_path}': {e}")

    return {item for item in itens if item}


def carregar_json(relative_path, default):
    path = resource_path(relative_path)
    if not os.path.exists(path):
        st.warning(f"Arquivo JSON nao encontrado: {path}")
        return default

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        st.warning(f"Erro ao decodificar JSON '{relative_path}': {e}")
    except Exception as e:
        st.warning(f"Erro ao carregar JSON '{relative_path}': {e}")

    return default


def normalizar_mapa(mapa):
    return {
        normalizar_palavra(chave): normalizar_palavra(valor)
        for chave, valor in mapa.items()
        if normalizar_palavra(chave) and normalizar_palavra(valor)
    }


def normalizar_lista(itens):
    return {normalizar_palavra(item) for item in itens if normalizar_palavra(item)}


def carregar_temas():
    temas_dir = resource_path("themes")
    temas = []

    if not os.path.isdir(temas_dir):
        st.warning(f"Diretorio de temas nao encontrado: {temas_dir}")
        return temas

    for filename in sorted(os.listdir(temas_dir)):
        if not filename.endswith(".json"):
            continue

        relative_path = os.path.join("themes", filename)
        dados = carregar_json(relative_path, {})
        if not dados:
            continue

        termos = normalizar_lista(dados.get("terms", []))
        correcoes = normalizar_mapa(dados.get("corrections", {}))
        protegidos = normalizar_lista(dados.get("protected_terms", []))
        nome = dados.get("name") or os.path.splitext(filename)[0].title()

        temas.append(
            {
                "id": os.path.splitext(filename)[0],
                "name": nome,
                "terms": termos,
                "corrections": correcoes,
                "protected_terms": protegidos,
            }
        )

    return temas


# --- Load Data --- Can be upgraded and have more items added
PALAVRAS_TECNICAS_LEGADO = carregar_palavras_tecnicas()
EXCECOES_SINGULAR = carregar_excecoes_singular()
STOPWORDS_GERAIS = (
    carregar_lista_texto("language/stopwords_pt.txt")
    | carregar_lista_texto("language/stopwords_en.txt")
)
PALAVRAS_BAIXO_VALOR = (
    carregar_lista_texto("language/low_value_words_pt.txt")
    | carregar_lista_texto("language/low_value_words_en.txt")
)
CORRECOES_GERAIS = normalizar_mapa(
    carregar_json("language/common_corrections.json", {})
)
TERMOS_CURTOS_PERMITIDOS = carregar_lista_texto("language/short_terms.txt")
TERMOS_PROTEGIDOS_GERAIS = carregar_lista_texto("language/protected_terms.txt")
TEMAS = carregar_temas()


# handle plural to singular expressions
def singularizar(palavra):
    if not isinstance(palavra, str) or not palavra:
        return palavra
    palavra_lower = palavra
    if palavra_lower in EXCECOES_SINGULAR:
        return EXCECOES_SINGULAR[palavra_lower]
    if palavra_lower in {"frances", "ingles", "portugues", "simples"}:
        return palavra_lower
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
    if palavra_lower.endswith(("gues", "ques")) and len(palavra_lower) > 5:
        return palavra_lower
    if palavra_lower.endswith("s") and len(palavra_lower) > 1:
        return palavra_lower[:-1]
    return palavra_lower


def corrigir_com_vocabulario(palavra, perfil):
    if not palavra or len(palavra) <= 2:
        return palavra
    if palavra in perfil["vocabulario_canonico"]:
        return perfil["vocabulario_canonico"][palavra]

    cutoff = 0.86 if len(palavra) <= 5 else 0.82
    candidatos = get_close_matches(palavra, perfil["vocabulario_fuzzy"], n=1, cutoff=cutoff)
    if candidatos:
        return perfil["vocabulario_canonico"][candidatos[0]]

    return palavra


# --- CSV Processing ---
def tokenizar_textos(textos):
    tokens = []
    for texto in textos:
        for palavra_original in str(texto).split():
            normalizada = normalizar_palavra(palavra_original)
            if normalizada:
                tokens.append(normalizada)
    return tokens


def contar_termos_compostos(tokens, termos):
    if not tokens:
        return 0

    texto_normalizado = " ".join(tokens)
    total = 0
    for termo in termos:
        if " " in termo:
            total += len(re.findall(rf"(?<!\w){re.escape(termo)}(?!\w)", texto_normalizado))
    return total


def detectar_tema(textos):
    tokens = tokenizar_textos(textos)
    tokens_relevantes = [
        token
        for token in tokens
        if token not in STOPWORDS_GERAIS and token not in PALAVRAS_BAIXO_VALOR
    ]
    contagem_tokens = pd.Series(tokens_relevantes).value_counts().to_dict()
    pontuacoes = []

    for tema in TEMAS:
        termos_tema = tema["terms"] | tema["protected_terms"] | set(tema["corrections"].values())
        score_bruto = 0

        for termo in termos_tema:
            if " " in termo:
                score_bruto += contar_termos_compostos(tokens, {termo}) * 4
            else:
                score_bruto += min(contagem_tokens.get(termo, 0), 8)

        # Larger theme packs should not win just because they contain more terms.
        normalizador = max(len(termos_tema) ** 0.35, 1)
        score = score_bruto / normalizador
        pontuacoes.append({"theme": tema, "score": score, "raw_score": score_bruto})

    pontuacoes.sort(key=lambda item: item["score"], reverse=True)
    melhor = pontuacoes[0] if pontuacoes else None

    if not melhor or melhor["raw_score"] == 0:
        return None, pontuacoes, 0

    segundo = pontuacoes[1] if len(pontuacoes) > 1 else {"score": 0}
    confianca = int(
        round(min(95, max(35, (melhor["score"] / (melhor["score"] + segundo["score"] + 0.01)) * 100)))
    )

    return melhor["theme"], pontuacoes, confianca


def construir_perfil_processamento(textos):
    tema, pontuacoes, confianca = detectar_tema(textos)
    termos = set(TERMOS_PROTEGIDOS_GERAIS)
    correcoes = dict(CORRECOES_GERAIS)
    stopwords = set(STOPWORDS_GERAIS)
    baixo_valor = set(PALAVRAS_BAIXO_VALOR)
    termos_curto = set(TERMOS_CURTOS_PERMITIDOS)

    if tema:
        termos |= tema["terms"] | tema["protected_terms"]
        correcoes.update(tema["corrections"])

        if tema["id"] == "tecnologia":
            termos |= PALAVRAS_TECNICAS_LEGADO

    vocabulario_canonico = {termo: termo for termo in termos if " " not in termo}
    vocabulario_composto = {termo: termo for termo in termos if " " in termo}
    correcoes_simples = {chave: valor for chave, valor in correcoes.items() if " " not in chave}
    correcoes_compostas = {chave: valor for chave, valor in correcoes.items() if " " in chave}

    return {
        "tema": tema,
        "tema_confianca": confianca,
        "tema_pontuacoes": pontuacoes,
        "stopwords": stopwords,
        "baixo_valor": baixo_valor,
        "correcoes": correcoes,
        "correcoes_simples": correcoes_simples,
        "correcoes_compostas": correcoes_compostas,
        "termos_curto": termos_curto,
        "termos": termos,
        "vocabulario_canonico": vocabulario_canonico,
        "vocabulario_composto": vocabulario_composto,
        "vocabulario_fuzzy": sorted(vocabulario_canonico),
    }


def corrigir_alias_comum(palavra, perfil):
    return perfil["correcoes_simples"].get(palavra, palavra)


def palavra_relevante(palavra, perfil):
    return palavra and palavra not in perfil["stopwords"] and palavra not in perfil["baixo_valor"] and (
        len(palavra) > 2 or palavra in perfil["termos_curto"]
    )


def conhecida_no_corretor(spell, palavra):
    return spell is not None and not spell.unknown([palavra])


def corrigir_palavra(palavra, perfil, spell_pt=None, spell_en=None):
    palavra = corrigir_alias_comum(palavra, perfil)
    if palavra in perfil["stopwords"] or palavra in perfil["baixo_valor"]:
        return palavra
    corrigida = corrigir_com_vocabulario(palavra, perfil)
    if corrigida != palavra or palavra in perfil["termos"]:
        return singularizar(corrigida)

    if conhecida_no_corretor(spell_en, palavra) or conhecida_no_corretor(spell_pt, palavra):
        return singularizar(palavra)

    if spell_pt:
        correcao = spell_pt.correction(palavra)
        if correcao:
            correcao = corrigir_alias_comum(normalizar_palavra(correcao), perfil)
            correcao = corrigir_com_vocabulario(correcao, perfil)
            return singularizar(correcao)

    return singularizar(palavra)


def combinar_termos_compostos(palavras, perfil, spell_pt=None, spell_en=None):
    termos = []
    index = 0
    max_partes = 4

    while index < len(palavras):
        termo_composto = None
        tamanho_composto = 0

        for tamanho in range(min(max_partes, len(palavras) - index), 1, -1):
            candidato = " ".join(palavras[index : index + tamanho])
            if candidato in perfil["correcoes_compostas"]:
                termo_composto = perfil["correcoes_compostas"][candidato]
                tamanho_composto = tamanho
                break
            if candidato in perfil["vocabulario_composto"]:
                termo_composto = perfil["vocabulario_composto"][candidato]
                tamanho_composto = tamanho
                break

        if termo_composto:
            termos.append(termo_composto)
            index += tamanho_composto
        else:
            palavra = corrigir_palavra(palavras[index], perfil, spell_pt, spell_en)
            if palavra_relevante(palavra, perfil):
                termos.append(palavra)
            index += 1

    return termos


def extrair_termos(texto, perfil, spell_pt=None, spell_en=None):
    palavras = []
    for palavra_original in str(texto).split():
        normalizada = normalizar_palavra(palavra_original)
        if not normalizada:
            continue
        palavras.append(normalizada)
    return combinar_termos_compostos(palavras, perfil, spell_pt, spell_en)


@st.cache_data  # Cache the processing result
def processar_csv(file_content):
    df = None
    spell_pt = None
    spell_en = None
    try:
        df = pd.read_csv(io.BytesIO(file_content))
    except Exception as e:
        st.error(f"Erro ao ler o arquivo CSV: {e}")
        return None, None, None

    if df.shape[1] < 2:
        st.error("CSV invalido: precisa ter pelo menos duas colunas.")
        return None, None, None

    segunda_coluna = df.iloc[:, 1]
    perfil = construir_perfil_processamento(segunda_coluna)

    try:
        spell_pt = SpellChecker(language="pt")
        spell_en = SpellChecker(language="en")
        if perfil["termos"]:
            spell_pt.word_frequency.load_words(perfil["termos"])
            spell_en.word_frequency.load_words(perfil["termos"])
    except Exception as e:
        # *** Use st.warning for non-critical errors like spellchecker init failure ***
        st.warning(
            f"Falha ao inicializar o corretor ortografico: {e}. Continuara sem correcao."
        )
        spell_pt = None
        spell_en = None

    termos_extraidos = []

    for texto in segunda_coluna:
        termos_extraidos.extend(extrair_termos(texto, perfil, spell_pt, spell_en))

    palavras_validas = [capitalizar(p) for p in termos_extraidos if p]
    if not palavras_validas:
        st.warning("Nenhuma palavra valida encontrada apos o processamento.")
        return {}, None, None

    frequencias = pd.Series(palavras_validas).value_counts()
    freq_df = pd.DataFrame(
        {"Palavra": frequencias.index, "Frequencia": frequencias.values}
    )
    tema_info = {
        "nome": perfil["tema"]["name"] if perfil["tema"] else "Generico",
        "confianca": perfil["tema_confianca"],
    }
    return frequencias.to_dict(), freq_df, tema_info


# --- Streamlit App Logic ---
st.title("☁️ Nuvem de Palavras")

# Initialize session state
if "frequencias" not in st.session_state:
    st.session_state.frequencias = None
if "freq_df" not in st.session_state:
    st.session_state.freq_df = None
if "tema_info" not in st.session_state:
    st.session_state.tema_info = None
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
            frequencias_calculadas, freq_df_calculado, tema_info = processar_csv(file_content)

            if frequencias_calculadas is not None:
                st.session_state.frequencias = frequencias_calculadas
                st.session_state.freq_df = freq_df_calculado
                st.session_state.tema_info = tema_info
                st.session_state.error_message = None
                st.rerun()
            else:
                # Error occurred during processing (should be shown by processar_csv)
                st.session_state.error_message = (
                    "Falha ao processar CSV. Verifique o arquivo ou os erros acima."
                )
                st.session_state.frequencias = None
                st.session_state.freq_df = None
                st.session_state.tema_info = None
                st.rerun()
else:
    # --- Results / Error View ---
    if st.session_state.error_message:
        st.error(st.session_state.error_message)
        if st.button("Tentar novamente com outro arquivo"):
            st.session_state.frequencias = None
            st.session_state.freq_df = None
            st.session_state.tema_info = None
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
