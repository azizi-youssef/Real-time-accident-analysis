import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time
import os
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="Prédiction des Accidents en Temps Réel",
    page_icon="🚗",
    layout="wide"
)

# Configuration de l'API
FLASK_API_URL = os.getenv('FLASK_API_URL', 'http://flask-api:5000')

# Titre
st.title("🚗 Dashboard de Prédiction des Accidents")

# Fonction pour récupérer les données
def get_latest_predictions():
    try:
        response = requests.get(f'{FLASK_API_URL}/predictions/latest', timeout=5)
        if response.status_code == 200:
            return response.json()['data']
        else:
            st.error(f"Erreur API: {response.status_code} - {response.text}")
        return []
    except requests.exceptions.ConnectionError:
        st.error(f"Impossible de se connecter à l'API Flask ({FLASK_API_URL}). Vérifiez que le service est en cours d'exécution.")
        return []
    except requests.exceptions.Timeout:
        st.warning("L'API met trop de temps à répondre. Nouvelle tentative dans 5 secondes...")
        return []
    except Exception as e:
        st.error(f"Erreur inattendue: {str(e)}")
        return []

def get_prediction_stats():
    try:
        response = requests.get(f'{FLASK_API_URL}/predictions/stats', timeout=5)
        if response.status_code == 200:
            return response.json()['data']
        else:
            st.error(f"Erreur API Stats: {response.status_code} - {response.text}")
        return {}
    except requests.exceptions.ConnectionError:
        st.error(f"Impossible de se connecter à l'API Flask ({FLASK_API_URL}) pour les statistiques.")
        return {}
    except requests.exceptions.Timeout:
        st.warning("L'API met trop de temps à répondre pour les statistiques.")
        return {}
    except Exception as e:
        st.error(f"Erreur inattendue lors de la récupération des statistiques: {str(e)}")
        return {}

# Création des colonnes pour le layout
col1, col2 = st.columns(2)

# Statut des services
with st.expander("📡 État des Services"):
    st.info("Tentative de connexion aux services...")
    
    # Vérification de l'API Flask
    try:
        response = requests.get(f'{FLASK_API_URL}/predictions/latest', timeout=2)
        st.success("✅ API Flask: Connectée")
    except:
        st.error("❌ API Flask: Non connectée")

# Création des conteneurs
map_placeholder = st.empty()
stats_placeholder = st.empty()
predictions_placeholder = st.empty()
time_placeholder = st.empty()

# Fonction pour générer une clé unique
def get_unique_key(base_key):
    return f"{base_key}_{int(time.time())}"

while True:
    current_time = datetime.now()
    
    # Récupération des données
    predictions = get_latest_predictions()
    stats = get_prediction_stats()
    
    # Mise à jour de l'interface
    with map_placeholder.container():
        st.subheader("📍 Carte des Accidents")
        if predictions:
            df = pd.DataFrame(predictions)
            fig_map = px.scatter_map(
                df,
                lat='latitude',
                lon='longitude',
                color='predicted_risk',
                hover_data=['timestamp', 'actual_severity'],
                zoom=3,
                title="Localisation des Accidents"
            )
            fig_map.update_layout(mapbox_style="open-street-map")
            st.plotly_chart(fig_map, use_container_width=True, key=get_unique_key("map"))
        else:
            st.warning("En attente de données... Vérifiez que le producteur Kafka et le traitement Spark sont actifs.")
    
    with stats_placeholder.container():
        st.subheader("📊 Statistiques")
        if stats:
            risk_counts = pd.Series(stats)
            fig_pie = px.pie(
                values=risk_counts.values,
                names=risk_counts.index,
                title="Distribution des Niveaux de Risque"
            )
            st.plotly_chart(fig_pie, use_container_width=True, key=get_unique_key("pie"))
        else:
            st.warning("Aucune statistique disponible pour le moment...")
    
    with predictions_placeholder.container():
        st.subheader("📝 Dernières Prédictions")
        if predictions:
            df = pd.DataFrame(predictions)
            st.dataframe(
                df[['timestamp', 'predicted_risk', 'actual_severity']].head(),
                use_container_width=True,
                key=get_unique_key("table")
            )
        else:
            st.info("Le système attend les premières prédictions d'accidents.")
    
    with time_placeholder.container():
        st.text(f"Dernière mise à jour: {current_time.strftime('%H:%M:%S')}")
    
    # Attente avant la prochaine mise à jour
    time.sleep(5) 