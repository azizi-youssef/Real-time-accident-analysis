FROM bitnami/spark:3.4.1

USER root

# Installation des dépendances système essentielles
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    python3-pip \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Mise à jour de pip et installation des dépendances de base
COPY requirements-spark-base.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements-spark-base.txt && \
    rm /tmp/requirements-spark-base.txt

# Installation des dépendances ML dans une couche séparée
COPY requirements-spark-ml.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements-spark-ml.txt && \
    rm /tmp/requirements-spark-ml.txt

# Ajout du script d'entrée
COPY docker/spark-entrypoint.sh /
RUN chmod +x /spark-entrypoint.sh

WORKDIR /app

ENTRYPOINT ["/spark-entrypoint.sh"]
