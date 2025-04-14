from backend.retinopathy_analyzer import RetinopathyAnalyzer
from backend.preprocess import resize_and_center_fundus
from PIL import Image
import streamlit as st
import requests
import io
import base64
import uuid
import numpy as np
import os

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

# CSS para tema claro
def light_theme():
    return """
        <style>
            #MainMenu, header, footer {visibility: hidden;}
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
            .image-preview {
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                max-width: 100px !important;
                width: 100% !important;
                margin: 0 auto !important;
                display: block !important;
            }
            .error-message { background-color: #fee2e2; padding: 10px; border-radius: 8px; }
            .success-message { background-color: #d1fae5; padding: 10px; border-radius: 8px; }
            body, .stApp { background-color: #ffffff; color: #1f2937; }
            div[data-testid="stImage"] {
                display: flex !important;
                justify-content: center !important;
                align-items: center !important;
            }
            div[data-testid="stImage"] img {
                max-width: 400px !important;
                width: 100% !important;
                height: auto !important;
                margin: 0 auto !important;
                display: block !important;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
        </style>
    """

# CSS para tema escuro
def dark_theme():
    return """
        <style>
            #MainMenu, header, footer {visibility: hidden;}
            .main { background-color: #374151; padding: 20px; border-radius: 10px; }
            .title { color: #60a5fa; font-weight: bold; }
            .subheader { color: #9ca3af; }
            .stButton>button {
                background-color: #60a5fa;
                color: #1f2937;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
            }
            .stButton>button:hover {
                background-color: #3b82f6;
                color: #ffffff;
                transition: 0.3s;
            }
            .stFileUploader { border: 2px dashed #4b5563; border-radius: 10px; padding: 10px; }
            .image-preview {
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                max-width: 100px !important;
                width: 100% !important;
                margin: 0 auto !important;
                display: block !important;
            }
            .error-message { background-color: #7f1d1d; color: #f3f4f6; padding: 10px; border-radius: 8px; }
            .success-message { background-color: #064e3b; color: #f3f4f6; padding: 10px; border-radius: 8px; }
            body, .stApp { background-color: #1f2937; color: #f3f4f6; }
            div[data-testid="stImage"] {
                display: flex !important;
                justify-content: center !important;
                align-items: center !important;
            }
            div[data-testid="stImage"] img {
                max-width: 400px !important;
                width: 100% !important;
                height: auto !important;
                margin: 0 auto !important;
                display: block !important;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            }
        </style>
    """

# Função para aplicar o tema com base no estado
def apply_theme():
    if st.session_state.theme == "dark":
        st.markdown(dark_theme(), unsafe_allow_html=True)
    else:
        st.markdown(light_theme(), unsafe_allow_html=True)

# Inicializar estado do tema
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# Inicializar chave do file_uploader
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = str(uuid.uuid4())

# Barra lateral com informações e botão de tema
with st.sidebar:
    st.header("Sobre")
    st.info("Este aplicativo utiliza IA para descrever imagens médicas. Desenvolvido pelo HCPA.")
    st.markdown("---")
    st.subheader("Configurações")
    # Botão para alternar tema
    if st.button("Tema Escuro" if st.session_state.theme == "light" else "Tema Claro"):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()

# Aplicar tema
apply_theme()

# Cabeçalho com logo
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

st.markdown("<p class='subheader'>Faça upload de uma imagem para análise.</p>", unsafe_allow_html=True)

# Container para upload e botões
with st.container():
    uploaded_file = st.file_uploader(
        "Escolha uma imagem (jpg, png, jpeg)",
        type=["jpg", "png", "jpeg"],
        help="Arraste e solte ou clique para selecionar.",
        key=st.session_state.uploader_key
    )

    # Exibir imagem se houver uma carregada
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Pré-visualização da imagem", use_container_width=True, output_format="auto", clamp=True, channels="RGB")

    # Botões Analisar e Limpar
    col1, col2 = st.columns(2)
    with col1:
        analyze_button = st.button("Analisar Imagem", key="analyze")
    with col2:
        clear_button = st.button("Limpar", key="clear")

    # Lógica do botão Limpar
    if clear_button:
        st.session_state.uploader_key = str(uuid.uuid4())  # Alterar a chave para recriar o file_uploader
        st.rerun()

    # Lógica do botão Analisar
    analyzer = RetinopathyAnalyzer("models/inceptionv3-1.0.0.keras")
    if analyze_button and uploaded_file is not None:
        with st.spinner("Analisando imagem..."):
            try:
                temp_dir = "temp_images"
                os.makedirs(temp_dir, exist_ok=True)
                
                # Generate a unique filename
                temp_image_path = os.path.join(temp_dir, f"upload_{uploaded_file.name}")
                
                # Save the uploaded image to a temporary file
                image.save(temp_image_path, format=image.format)
                
                # Process the image using the file path
                processed_image = resize_and_center_fundus(save_path=temp_image_path, image_path=temp_image_path)
                
                # # Initialize analyzer and make prediction
                if(processed_image):
                    processed_filename = f"upload_{uploaded_file.name}"
                    processed_image_path = os.path.join(temp_dir, processed_filename)
                    processed_image = Image.open(processed_image_path)
                    processed_array = np.array(processed_image)
                    processed_array = np.expand_dims(processed_array, axis=0)
                    prediction = analyzer.predict(processed_array)

                # Exibição do resultado
                st.markdown("<div class='success-message'>✅ Análise concluída com sucesso!</div>", unsafe_allow_html=True)
                st.markdown("### Descrição da Imagem")
                st.markdown(f"<div style='padding: 15px; border-radius: 8px;'>Predição do modelo: {prediction[0][0]}</div>", unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f"<div class='error-message'>❌ Erro ao processar imagem: {str(e)}</div>", unsafe_allow_html=True)
            finally:
                for temp_file in [temp_image_path, processed_image_path]:
                    if 'temp_file' in locals() and os.path.exists(temp_file):
                        os.remove(temp_file)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #6b7280;'>HCPA © 2025</p>", unsafe_allow_html=True)