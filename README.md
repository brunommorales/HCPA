# HCPA - Predição do encaminhamento de retinopatia diabética

Este projeto permite fazer upload de uma imagem e obter uma predição de encaminhamento gerada pelo InceptionV3, usando uma interface web interativa com Streamlit.

## 🔧 Como executar

Clone o repositório:
```bash
git clone https://github.com/brunommorales/HCPA.git
cd HCPA
pip install -r requirements.txt
streamlit run hcpa.py
```

Docker:
```bash
docker build -t hcpa-app .
docker run -p 8501:8501 hcpa-app
```
