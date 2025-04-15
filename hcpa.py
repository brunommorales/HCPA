from backend.retinopathy_analyzer import RetinopathyAnalyzer
from backend.preprocess import resize_and_center_fundus
from PIL import Image
import streamlit as st
import base64
import uuid
import numpy as np
import os
import tempfile

# Configuração da página
st.set_page_config(page_title="HCPA", layout="centered")

# ============================ FUNÇÕES AUXILIARES ============================

def get_base64_of_image(image_path):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        st.warning("Imagem do logo não encontrada. Usando placeholder.")
        return ""

def apply_theme():
    css_file = "styles/dark.css" if st.session_state.theme == "dark" else "styles/light.css"
    with open(css_file, "r") as f:
        css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def initialize_states():
    st.session_state.setdefault("theme", "light")
    st.session_state.setdefault("uploader_key", str(uuid.uuid4()))
    st.session_state.setdefault("uploaded_file", None)
    st.session_state.setdefault("preprocessed_path", None)

def show_header(image_path):
    image_base64 = get_base64_of_image(image_path)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h1 class='title'>Predição do Encaminhamento de Retinopatia Diabética</h1>", unsafe_allow_html=True)
    with col2:
        if image_base64:
            st.markdown(f"<img src='data:image/png;base64,{image_base64}' style='height: 168px;'>", unsafe_allow_html=True)

def clear_file_uploader():
    st.session_state["uploader_key"] = str(uuid.uuid4())
    st.session_state["uploaded_file"] = None
    st.session_state["preprocessed_path"] = None

def preprocess_uploaded_image(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        image = Image.open(uploaded_file)
        image.save(tmp.name)

        success = resize_and_center_fundus(save_path=tmp.name, image_path=tmp.name)
        if not success:
            st.error("Falha ao pré-processar a imagem.")
            return None

        return tmp.name  # Path to preprocessed image

def analyze_image(image_path, analyzer):
    with st.spinner("Analisando imagem..."):
        try:
            processed_image = Image.open(image_path)
            processed_array = np.expand_dims(np.array(processed_image), axis=0)

            prediction = analyzer.predict(processed_array)

            st.markdown("<div class='success-message'>✅ Análise concluída com sucesso!</div>", unsafe_allow_html=True)
            st.markdown("### Descrição da Imagem")
            st.markdown(f"<div style='padding: 15px; border-radius: 8px;'>Predição do modelo: {prediction[0][0]}</div>", unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f"<div class='error-message'>❌ Erro ao processar imagem: {str(e)}</div>", unsafe_allow_html=True)

# ============================ INICIALIZAÇÃO ============================

initialize_states()
apply_theme()

# ============================ SIDEBAR ============================

with st.sidebar:
    st.header("Sobre")
    st.info("Este aplicativo utiliza IA para descrever imagens médicas. Desenvolvido pelo HCPA.")
    st.subheader("Configurações")
    if st.button("Tema Escuro" if st.session_state.theme == "light" else "Tema Claro"):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()

# ============================ TOPO ============================

show_header("images/hcpa.jpg")
st.markdown("<p class='subheader'>Faça upload de uma imagem para análise.</p>", unsafe_allow_html=True)

# ============================ UPLOAD ============================

uploaded_file = st.file_uploader(
    "Escolha uma imagem (jpg, png, jpeg)",
    type=["jpg", "png", "jpeg"],
    help="Arraste e solte ou clique para selecionar.",
    key=st.session_state["uploader_key"]
)

if uploaded_file:
    st.session_state["uploaded_file"] = uploaded_file
    st.image(Image.open(uploaded_file), caption="Pré-visualização da imagem", use_container_width=True)

    # Pré-processamento imediato
    st.session_state["preprocessed_path"] = preprocess_uploaded_image(uploaded_file)

# ============================ BOTÕES ============================

col1, col2 = st.columns(2)
with col1:
    analyze_button = st.button("Analisar Imagem", key="analyze")
with col2:
    if st.button("Limpar", key="clear"):
        clear_file_uploader()

# ============================ ANÁLISE ============================

analyzer = RetinopathyAnalyzer("models/inceptionv3-1.0.0.keras")

if analyze_button and st.session_state.get("preprocessed_path"):
    analyze_image(st.session_state["preprocessed_path"], analyzer)

# ============================ RODAPÉ ============================

st.markdown("---")
st.markdown("<p style='text-align: center; color: #6b7280;'>HCPA © 2025</p>", unsafe_allow_html=True)
