# Projet Big Data - Prédiction des Accidents en Temps Réel

Ce projet utilise des technologies Big Data pour analyser et prédire en temps réel les accidents de la route aux États-Unis.

## 🏗️ Architecture

- **Kafka** : Streaming de données
- **Spark Streaming** : Traitement en temps réel
- **LSTM (TensorFlow)** : Modèle de prédiction
- **Cassandra** : Stockage des résultats
- **Flask** : API REST
- **Streamlit** : Dashboard en temps réel

## 🚀 Installation

1. Assurez-vous d'avoir Docker et Docker Compose installés
2. Clonez ce repository
3. Lancez les services :
```bash
docker-compose up -d
```

## 📂 Structure du Projet

```
.
├── data/                      # Données brutes et transformées
├── kafka_producer/           # Producer Kafka
├── spark_streaming/         # Scripts Spark Streaming
├── model/                   # Modèle LSTM
├── api/                     # API Flask
├── dashboard/              # Dashboard Streamlit
├── docker/                 # Dockerfiles
└── docker-compose.yml     # Configuration Docker Compose
```

## 🔧 Services

- Kafka : `localhost:9092`
- API Flask : `localhost:5000`
- Dashboard Streamlit : `localhost:8501`
- Cassandra : `localhost:9042`

## 📊 Fonctionnalités

1. Streaming de données d'accidents via Kafka
2. Prédiction en temps réel avec LSTM
3. Visualisation des prédictions sur dashboard
4. API REST pour accéder aux données

## 🛠️ Technologies Utilisées

- Python 3.9
- Apache Kafka
- Apache Spark
- TensorFlow/Keras
- Apache Cassandra
- Flask
- Streamlit
- Docker & Docker Compose 