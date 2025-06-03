FROM python:3.9-slim

WORKDIR /app

# Installation des dépendances Python avec timeout augmenté
COPY requirements-kafka.txt /app/
RUN pip install --no-cache-dir --default-timeout=100 -r requirements-kafka.txt

# Le script sera monté via un volume
CMD ["python", "src/producer.py"] 