FROM python:3.9-slim

WORKDIR /app

# Installation des dépendances Python avec timeout augmenté
COPY requirements-api.txt /app/
RUN pip install --no-cache-dir --default-timeout=100 -r requirements-api.txt

# Le script sera monté via un volume
EXPOSE 5000

CMD ["python", "src/app.py"] 