from flask import Flask, jsonify
from cassandra.cluster import Cluster, NoHostAvailable
from flask_cors import CORS
from datetime import datetime, timedelta
import time
import os

app = Flask(__name__)
CORS(app)

# Configuration Cassandra depuis les variables d'environnement
CASSANDRA_HOST = os.getenv('CASSANDRA_HOST', 'cassandra')
CASSANDRA_PORT = int(os.getenv('CASSANDRA_PORT', 9042))

def wait_for_cassandra():
    """Attend que Cassandra soit disponible"""
    max_retries = 10
    retry_interval = 5
    
    for i in range(max_retries):
        try:
            cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)
            session = cluster.connect()
            print(f"Connexion à Cassandra établie sur {CASSANDRA_HOST}:{CASSANDRA_PORT}")
            return session, cluster
        except NoHostAvailable:
            if i < max_retries - 1:
                print(f"Tentative de connexion à Cassandra échouée. Nouvelle tentative dans {retry_interval} secondes...")
                time.sleep(retry_interval)
            else:
                raise Exception("Impossible de se connecter à Cassandra après plusieurs tentatives")

def get_cassandra_session():
    """Établit une connexion à Cassandra"""
    try:
        cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)
        session = cluster.connect()
        return session, cluster
    except Exception as e:
        print(f"Erreur de connexion à Cassandra: {str(e)}")
        raise

@app.route('/predictions/latest', methods=['GET'])
def get_latest_predictions():
    """Récupère les dernières prédictions"""
    session, cluster = get_cassandra_session()
    
    try:
        # Récupération des 50 dernières prédictions
        rows = session.execute("""
            SELECT predicted_risk, id, timestamp, latitude, longitude, actual_severity
            FROM accidents.predictions
            LIMIT 50
            ALLOW FILTERING
        """)
        
        predictions = []
        for row in rows:
            predictions.append({
                'predicted_risk': row.predicted_risk,
                'id': str(row.id),
                'timestamp': row.timestamp.isoformat() if row.timestamp else None,
                'latitude': float(row.latitude),
                'longitude': float(row.longitude),
                'actual_severity': row.actual_severity
            })
        
        return jsonify({
            'status': 'success',
            'data': predictions
        })
    
    except Exception as e:
        print(f"Erreur lors de la récupération des prédictions: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    
    finally:
        cluster.shutdown()

@app.route('/predictions/stats', methods=['GET'])
def get_prediction_stats():
    """Récupère des statistiques sur les prédictions"""
    session, cluster = get_cassandra_session()
    
    try:
        # Récupération de tous les niveaux de risque distincts
        risk_levels = session.execute("""
            SELECT predicted_risk, COUNT(*) as count
            FROM accidents.predictions
            GROUP BY predicted_risk
            ALLOW FILTERING
        """)
        
        risk_stats = {}
        for row in risk_levels:
            risk_stats[row.predicted_risk] = row.count
        
        return jsonify({
            'status': 'success',
            'data': risk_stats
        })
    
    except Exception as e:
        print(f"Erreur lors de la récupération des statistiques: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    
    finally:
        cluster.shutdown()

if __name__ == '__main__':
    # Attendre que Cassandra soit disponible avant de démarrer
    session, cluster = wait_for_cassandra()
    cluster.shutdown()
    
    # Démarrer l'application Flask
    app.run(host='0.0.0.0', port=5000) 