import streamlit as st
import requests
from PIL import Image
import io
import base64

# Configuração inicial da página
st.set_page_config(page_title="HCPA - Diagnósticos de Imagens", layout="centered")

# Função para converter imagem em base64
def get_base64_of_image(image_path):
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        st.warning("Imagem do logo não encontrada. Usando placeholder.")
        return ""

# CSS para temas claro e escuro
def apply_theme(theme):
    if theme == "Escuro":
        st.markdown("""
            <style>
                .main { background-color: #1f2937; padding: 20px; border-radius: 10px; }
                .title, .subheader, h1, h2, h3, p, div, span, label {
                    color: #e5e7eb !important;
                }
                .stButton>button {
                    background-color: #3b82f6;
                    color: white;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                }
                .stButton>button:hover {
                    background-color: #60a5fa;
                    transition: 0.3s;
                }
                .stFileUploader { 
                    border: 2px dashed #4b5563; 
                    border-radius: 10px; 
                    padding: 10px; 
                    background-color: #374151;
                }
                .image-preview { border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.3); }
                .error-message { background-color: #991b1b; padding: 10px; border-radius: 8px; color: white; }
                .success-message { background-color: #15803d; padding: 10px; border-radius: 8px; color: white; }
                .stMarkdown, .stText { background-color: #374151; padding: 10px; border-radius: 8px; }
                body, .stApp { background-color: #111827; }
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
                .main { background-color: #f5f7fa; padding: 20px; border-radius: 10px; }
                .title { color: #1e3a8a; font-weight: bold; }
                .subheader { color: #4b5e8e; }
                .stButton>button {
                    background-color: #1e3a8a;
                    color: white;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                }
                .stButton>button:hover {
                    background-color: #3b82f6;
                    transition: 0.3s;
                }
                .stFileUploader { border: 2px dashed #d1d5db; border-radius: 10px; padding: 10px; }
                .image-preview { border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
                .error-message { background-color: #fee2e2; padding: 10px; border-radius: 8px; }
                .success-message { background-color: #d1fae5; padding: 10px; border-radius: 8px; }
                body, .stApp { background-color: #ffffff; }
            </style>
        """, unsafe_allow_html=True)

# Barra lateral com seleção de tema
with st.sidebar:
    st.header("Sobre")
    st.info("Este aplicativo utiliza IA para descrever imagens médicas ou gerais. Desenvolvido pelo HCPA.")
    st.markdown("---")
    st.subheader("Configurações")
    theme = st.selectbox("Tema", ["Claro", "Escuro"])
    apply_theme(theme)

# Resto do código (mantido como no original, com o cabeçalho, upload e análise)
image_path = "images/image_hcpa.png"
image_base64 = get_base64_of_image(image_path)

with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h1 class='title'>HCPA - Diagnóstico de Imagens</h1>", unsafe_allow_html=True)
    with col2:
        if image_base64:
            st.markdown(
                f"<img src='data:image/png;base64,{image_base64}' style='height: 60px; vertical-align: middle;'>",
                unsafe_allow_html=True
            )

st.markdown("<p class='subheader'>Faça upload de uma imagem para análise automática com inteligência artificial.</p>", unsafe_allow_html=True)

with st.container():
    uploaded_file = st.file_uploader(
        "Escolha uma imagem (jpg, png, jpeg)",
        type=["jpg", "png", "jpeg"],
        help="Arraste e solte ou clique para selecionar."
    )

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Pré-visualização da imagem", use_column_width=True, output_format="auto", clamp=True)

        col1, col2 = st.columns(2)
        with col1:
            analyze_button = st.button("Analisar Imagem", key="analyze")
        with col2:
            clear_button = st.button("Limpar", key="clear")

        if clear_button:
            st.session_state.uploaded_file = None
            st.rerun()

        if analyze_button:
            with st.spinner("Analisando imagem..."):
                try:
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format=image.format)
                    img_byte_arr = img_byte_arr.getvalue()

                    files = {"file": (uploaded_file.name, img_byte_arr, uploaded_file.type)}
                    response = requests.post("http://localhost:8000/analyze", files=files)

                    if response.status_code == 200:
                        result = response.json()
                        st.markdown("<div class='success-message'>✅ Análise concluída com sucesso!</div>", unsafe_allow_html=True)
                        st.markdown("### Descrição da Imagem")
                        st.markdown(f"<div style='padding: 15px; border-radius: 8px;'>{result['description']}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='error-message'>❌ Erro: {response.json().get('detail', 'Falha na análise')}</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f"<div class='error-message'>❌ Erro ao conectar com o backend: {str(e)}</div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #6b7280;'>HCPA © 2025</p>", unsafe_allow_html=True)