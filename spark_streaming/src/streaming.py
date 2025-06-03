import os
import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, udf, to_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType
import tensorflow as tf
from tensorflow.keras.models import load_model
from cassandra.cluster import Cluster
from datetime import datetime
import logging
import sys
from uuid import uuid5, NAMESPACE_DNS

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Définition du schéma des données Kafka
kafka_schema = StructType([
    StructField("id", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("latitude", DoubleType(), True),
    StructField("longitude", DoubleType(), True),
    StructField("severity", IntegerType(), True),
    StructField("event_time", StringType(), True)
])

# Chargement du modèle ML en tant que variable globale
try:
    logger.info("Chargement du modèle ML...")
    model = load_model('/model/accident_predictor.h5')
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    logger.info("Modèle ML chargé avec succès")
except Exception as e:
    logger.error(f"Erreur lors du chargement du modèle : {str(e)}")
    raise e

def predict_risk(latitude, longitude):
    """Prédiction du risque d'accident"""
    try:
        logger.info(f"Prédiction pour lat={latitude}, lon={longitude}")
        # Préparation des données avec la bonne forme (None, 1, 2)
        input_data = tf.convert_to_tensor([[float(latitude), float(longitude)]])
        input_data = tf.expand_dims(input_data, axis=1)  # Ajoute une dimension pour obtenir (None, 1, 2)
        
        # Prédiction avec le modèle
        prediction = model.predict(input_data, verbose=0)
        
        # Conversion de la prédiction en catégorie de risque
        risk_value = float(prediction[0][0])
        if risk_value < 0.3:
            risk_category = "LOW"
        elif risk_value < 0.7:
            risk_category = "MEDIUM"
        else:
            risk_category = "HIGH"
        
        result = {
            "category": risk_category,
            "value": risk_value
        }
        logger.info(f"Prédiction effectuée : {result}")
        return json.dumps(result)
    except Exception as e:
        logger.error(f"Erreur lors de la prédiction : {str(e)}")
        return json.dumps({
            "category": "ERROR",
            "value": 0.0
        })

def process_batch(batch_df, batch_id):
    try:
        # Connexion à Cassandra
        cluster = Cluster(['cassandra'])
        session = cluster.connect()
        
        # Création du keyspace et de la table si nécessaires
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS accidents
            WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
        """)
        
        session.execute("""
            CREATE TABLE IF NOT EXISTS accidents.predictions (
                predicted_risk text,
                id uuid,
                actual_severity int,
                event_time timestamp,
                latitude double,
                longitude double,
                timestamp timestamp,
                PRIMARY KEY (predicted_risk, id)
            ) WITH CLUSTERING ORDER BY (id ASC)
        """)
        
        # Traitement de chaque ligne
        for row in batch_df.collect():
            try:
                # Prédiction directement avec les coordonnées
                risk_prediction = predict_risk(row.latitude, row.longitude)
                risk_data = json.loads(risk_prediction)
                
                # Génération d'un UUID à partir de l'ID de l'accident
                accident_uuid = uuid5(NAMESPACE_DNS, str(row.id))
                event_time = datetime.now()
                
                # Préparation de la requête d'insertion
                query = """
                    INSERT INTO accidents.predictions (
                        predicted_risk, id, timestamp, latitude, longitude, actual_severity, event_time
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    risk_data['category'],
                    accident_uuid,
                    datetime.now(),
                    float(row.latitude),
                    float(row.longitude),
                    int(row.severity),
                    event_time
                )
                
                # Exécution de la requête
                session.execute(query, params)
                logger.info(f"Données insérées avec succès pour l'ID {row.id}")
                
            except Exception as e:
                logger.error(f"Erreur lors de l'insertion des données pour l'ID {row.id} : {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Erreur lors du traitement du batch {batch_id} : {str(e)}")
    finally:
        if 'cluster' in locals():
            cluster.shutdown()

def create_spark_session():
    """Création de la session Spark"""
    return SparkSession.builder \
        .appName("AccidentRiskPrediction") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1") \
        .config("spark.streaming.kafka.consumer.cache.enabled", "false") \
        .config("spark.streaming.stopGracefullyOnShutdown", "true") \
        .config("spark.sql.shuffle.partitions", "2") \
        .config("spark.default.parallelism", "2") \
        .getOrCreate()

def main():
    """Fonction principale"""
    try:
        # Création de la session Spark
        spark = create_spark_session()
        logger.info("Session Spark créée avec succès")
        
        # Lecture du flux Kafka
        logger.info("Configuration de la lecture du flux Kafka...")
        df = spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", "kafka:9092") \
            .option("subscribe", "accidents") \
            .option("startingOffsets", "earliest") \
            .option("failOnDataLoss", "false") \
            .option("maxOffsetsPerTrigger", "100") \
            .load()
        logger.info("Flux Kafka configuré avec succès")
        
        # Parsing des données JSON
        parsed_df = df.select(
            from_json(col("value").cast("string"), kafka_schema).alias("data")
        ).select("data.*")
        
        # Création de l'UDF pour la prédiction
        predict_risk_udf = udf(predict_risk, StringType())
        
        # Application de la prédiction
        result_df = parsed_df.withColumn(
            "risk_prediction",
            predict_risk_udf(col("latitude"), col("longitude"))
        )
        
        # Écriture des résultats dans Cassandra
        logger.info("Démarrage du streaming...")
        query = result_df \
            .writeStream \
            .foreachBatch(process_batch) \
            .outputMode("append") \
            .trigger(processingTime="5 seconds") \
            .start()
        
        logger.info("Streaming démarré avec succès")
        query.awaitTermination()
        
    except Exception as e:
        logger.error(f"Erreur dans la fonction principale : {str(e)}")
        raise e

if __name__ == "__main__":
    main()
