import json
import time
import os
import pandas as pd
from kafka import KafkaProducer
from datetime import datetime

def create_producer(max_retries=5, retry_interval=10):
    """Crée et retourne un producteur Kafka avec retries"""
    for i in range(max_retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=['kafka:9092'],
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
            print("Connexion à Kafka établie avec succès")
            return producer
        except Exception as e:
            if i < max_retries - 1:
                print(f"Tentative de connexion à Kafka échouée ({str(e)}). Nouvelle tentative dans {retry_interval} secondes...")
                time.sleep(retry_interval)
            else:
                raise Exception(f"Impossible de se connecter à Kafka après {max_retries} tentatives")

def read_and_send_data(producer, csv_path, topic_name='accidents'):
    """Lit le fichier CSV et envoie les données à Kafka en boucle"""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Le fichier {csv_path} n'existe pas")
    
    print(f"Lecture du fichier : {csv_path}")
    
    # Liste des encodages à essayer
    encodings = ['utf-8', 'latin1', 'cp1252', 'ISO-8859-1']
    
    for encoding in encodings:
        try:
            print(f"Tentative de lecture avec l'encodage : {encoding}")
            # Lecture du CSV avec les colonnes importantes
            df = pd.read_csv(csv_path, 
                           usecols=['ID', 'Start_Time', 'Start_Lat', 'Start_Lng', 'Severity'],
                           encoding=encoding)
            print(f"Lecture réussie avec l'encodage : {encoding}")
            break
        except UnicodeDecodeError:
            print(f"Échec de lecture avec l'encodage : {encoding}")
            if encoding == encodings[-1]:
                raise Exception("Impossible de lire le fichier avec les encodages disponibles")
            continue
    
    print(f"Nombre total d'accidents à envoyer : {len(df)}")
    
    while True:  # Boucle infinie pour continuer à envoyer les données
        print("\nDémarrage d'un nouveau cycle d'envoi de données...")
        for _, row in df.iterrows():
            try:
                # Création du message
                message = {
                    'id': row['ID'],
                    'timestamp': row['Start_Time'],
                    'latitude': float(row['Start_Lat']),
                    'longitude': float(row['Start_Lng']),
                    'severity': int(row['Severity']),
                    'event_time': datetime.now().isoformat()
                }
                
                # Envoi du message
                producer.send(topic_name, value=message)
                print(f"Message envoyé : {message['id']}")
                
                # Attente d'une seconde entre chaque message pour simuler le temps réel
                time.sleep(1)
                
            except Exception as e:
                print(f"Erreur lors de l'envoi du message {row['ID']}: {str(e)}")
                continue
        
        print("Cycle d'envoi terminé, pause de 5 secondes avant le prochain cycle...")
        time.sleep(5)  # Pause entre les cycles

def main():
    """Fonction principale"""
    csv_path = '/data/US_Accidents_filtered.csv'
    producer = None
    
    try:
        # Vérification de l'existence du fichier
        if not os.path.exists(csv_path):
            print(f"Erreur : Le fichier {csv_path} n'existe pas")
            print(f"Contenu du répertoire /data : {os.listdir('/data')}")
            return
        
        # Création du producteur
        producer = create_producer()
        
        # Lecture et envoi des données
        read_and_send_data(producer, csv_path)
        
    except Exception as e:
        print(f"Erreur : {str(e)}")
    
    finally:
        if producer:
            producer.close()
            print("Producteur Kafka fermé")

if __name__ == "__main__":
    # Attente de 30 secondes pour s'assurer que Kafka est prêt
    print("Attente du démarrage de Kafka...")
    time.sleep(30)
    main() 