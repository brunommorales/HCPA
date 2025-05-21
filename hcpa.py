from backend.retinopathy_analyzer import RetinopathyAnalyzer
from backend.preprocess import resize_and_center_fundus_in_memory
from PIL import Image, UnidentifiedImageError
import streamlit as st
import base64
import uuid
import numpy as np

# ============================ PAGE CONFIG ============================
st.set_page_config(page_title="HCPA - Retinopatia", layout="centered")

# ============================ HELPER FUNCTIONS ============================
def filter_valid_images(files):
    """Filter uploaded files to include only valid image files."""
    valid_extensions = ('.jpg', '.jpeg', '.png')
    return [file for file in files if file.name.lower().endswith(valid_extensions)]

@st.cache_data
def get_base64_of_image(image_path):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        st.warning("Logo não encontrada.")
        return ""

def apply_theme():
    css_file = "styles/dark.css" if st.session_state.theme == "dark" else "styles/light.css"
    with open(css_file, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def initialize_states():
    st.session_state.setdefault("theme", "light")
    st.session_state.setdefault("uploader_key", str(uuid.uuid4()))
    st.session_state.setdefault("uploaded_files", None)
    st.session_state.setdefault("analysis_results", None)

def show_header(image_path):
    image_base64 = get_base64_of_image(image_path)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h1 class='title'>Predição do Encaminhamento de Retinopatia Diabética</h1>", unsafe_allow_html=True)
    with col2:
        if image_base64:
            st.markdown(f"<img src='data:image/png;base64,{image_base64}' style='height: 168px;'>", unsafe_allow_html=True)

def preprocess_uploaded_image(uploaded_file):
    try:
        pil_image = Image.open(uploaded_file).convert("RGB")
        processed = resize_and_center_fundus_in_memory(pil_image, diameter=299)
        return Image.fromarray(processed) if processed is not None else None
    except UnidentifiedImageError:
        st.error(f"{uploaded_file.name} não é uma imagem válida.")
        return None

def analyze_single_image(pil_image, analyzer):
    with st.spinner("Analisando imagem..."):
        try:
            processed_array = np.expand_dims(np.array(pil_image), axis=0)
            prediction = analyzer.predict(processed_array)
            return prediction[0][0]
        except Exception as e:
            st.error(f"Erro ao processar imagem: {str(e)}")
            return None

def get_recommendation(probability):
    if probability >= 0.8:
        return "🔴 **Alta recomendação de encaminhamento.**", "#ef4444"
    elif 0.5 <= probability < 0.8:
        return "🟠 **Recomendação moderada de encaminhamento.**", "#f59e0b"
    else:
        return "🟢 **Baixa recomendação de encaminhamento.**", "#22c55e"

def display_single_result(prob):
    recommendation, color = get_recommendation(prob)
    st.markdown(f"""
        <div style='background-color: {color}20; border-left: 5px solid {color}; padding: 15px; border-radius: 8px;'>
            <strong>✅ Resultado:</strong><br>
            📈 Probabilidade: <strong>{prob:.2%}</strong><br>
            {recommendation}
        </div>
    """, unsafe_allow_html=True)

def display_batch_results(results):
    probabilities = [result['probability'] for result in results]
    stats = {
        "Média": np.mean(probabilities),
        "Mediana": np.median(probabilities),
        "Mínima": min(probabilities),
        "Máxima": max(probabilities)
    }
    
    st.subheader("Estatísticas do Lote")
    cols = st.columns(4)
    for (name, value), col in zip(stats.items(), cols):
        with col:
            st.metric(name, f"{value:.2%}")

    with st.expander("🔍 Ver Resultados Detalhados", expanded=False):
        for result in results:
            risk_class = "high-risk" if result['probability'] >= 0.8 else \
                       "moderate-risk" if result['probability'] >= 0.5 else "low-risk"
            
            with st.container():
                st.markdown("<div class='result-container'>", unsafe_allow_html=True)
                cols = st.columns([1, 3])
                with cols[0]:
                    st.image(result['image'], use_container_width=True)
                with cols[1]:
                    st.markdown(f"""
                        <div class='result-info'>
                            <strong>{result['filename']}</strong><br>
                            <span class='{risk_class}'>
                                Probabilidade: <strong>{result['probability']:.2%}</strong>
                            </span>
                        </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

# ============================ INITIALIZATION ============================
initialize_states()
apply_theme()

# ============================ SIDEBAR ============================
# ============================ SIDEBAR ============================
with st.sidebar:
    st.header("Sobre")
    st.info("Sistema de predição de encaminhamento para retinopatia diabética.")
    
    current_theme = st.session_state.get("theme", "light")
    
    theme = st.selectbox(
        "Tema", 
        ["Claro", "Escuro"], 
        index=0 if current_theme == "light" else 1,
        key="theme_select"
    )
    
    new_theme = "light" if theme == "Claro" else "dark"
    if new_theme != current_theme:
        st.session_state.theme = new_theme
        st.rerun()

# ============================ MAIN CONTENT ============================
show_header("images/hcpa.jpg")
st.markdown("<p class='subheader'>Carregue imagens de retina para análise</p>", unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Selecione imagens (JPG/PNG)",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    key=st.session_state["uploader_key"]
)

if uploaded_files:
    valid_files = filter_valid_images(uploaded_files)
    if valid_files:
        st.session_state["uploaded_files"] = valid_files
        st.success(f"{len(valid_files)} imagem(ns) válida(s)")
        
        preview_cols = st.columns(min(4, len(valid_files)))
        for i, file in enumerate(valid_files[:4]):
            with preview_cols[i % 4]:
                st.image(Image.open(file), use_container_width=True)
        
        if len(valid_files) > 4:
            st.info(f"+ {len(valid_files)-4} imagens adicionais")

# ============================ MODEL & ANALYSIS ============================
@st.cache_resource
def load_model():
    return RetinopathyAnalyzer("models/inceptionv3-1.0.0.keras")

analyzer = load_model()

if st.button("Analisar Imagens", type="primary") and st.session_state.get("uploaded_files"):
    results = []
    progress_bar = st.progress(0)
    
    for i, file in enumerate(st.session_state["uploaded_files"]):
        try:
            original_img = Image.open(file).convert("RGB")
            processed_img = preprocess_uploaded_image(file)
            
            if processed_img:
                prob = analyze_single_image(processed_img, analyzer)
                if prob is not None:
                    results.append({
                        "filename": file.name,
                        "image": original_img,
                        "probability": prob
                    })
            
            progress_bar.progress((i + 1) / len(st.session_state["uploaded_files"]))
        except Exception as e:
            st.error(f"Erro processando {file.name}: {str(e)}")
    
    if results:
        st.session_state["analysis_results"] = results
        if len(results) == 1:
            display_single_result(results[0]["probability"])
        else:
            display_batch_results(results)

# ============================ FOOTER ============================
st.markdown("---")