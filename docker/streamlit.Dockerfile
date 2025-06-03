FROM python:3.9-slim

WORKDIR /app

# Mise à jour de pip
RUN python -m pip install --upgrade pip

# Installation des dépendances de base
RUN pip install --no-cache-dir \
    numpy>=1.23.5 \
    pandas>=2.0.1 \
    python-dotenv>=1.0.0 \
    requests>=2.31.0

# Installation des dépendances de visualisation
RUN pip install --no-cache-dir \
    plotly>=5.14.1 \
    pillow>=6.2.0

# Installation de Streamlit et ses dépendances
RUN pip install --no-cache-dir \
    streamlit>=1.22.0 \
    pyarrow>=4.0.0 \
    click>=7.0 \
    rich>=10.11.0 \
    toml>=0.10.2 \
    tenacity>=8.0.0

# Le script sera monté via un volume
EXPOSE 8501

CMD ["streamlit", "run", "src/dashboard.py"] 