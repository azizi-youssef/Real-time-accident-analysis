import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import joblib

def prepare_data(df):
    """Prépare les données pour le modèle LSTM"""
    # Sélection des features
    features = ['Start_Lat', 'Start_Lng']
    X = df[features].values
    
    # Normalisation des features
    scaler_X = MinMaxScaler()
    X_scaled = scaler_X.fit_transform(X)
    
    # Préparation de la target (Severity)
    y = df['Severity'].values - 1  # 0-based indexing
    
    # Reshape pour LSTM [samples, time steps, features]
    X_reshaped = X_scaled.reshape((X_scaled.shape[0], 1, X_scaled.shape[1]))
    
    return X_reshaped, y, scaler_X

def create_model(input_shape, num_classes=4):
    """Crée le modèle LSTM"""
    model = Sequential([
        LSTM(64, input_shape=input_shape, return_sequences=True),
        Dropout(0.2),
        LSTM(32),
        Dropout(0.2),
        Dense(16, activation='relu'),
        Dense(num_classes, activation='softmax')
    ])
    
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model

def train_and_save_model():
    """Entraîne et sauvegarde le modèle"""
    # Chargement des données
    df = pd.read_csv('/data/US_Accidents_22_23.csv')
    
    # Préparation des données
    X, y, scaler = prepare_data(df)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Création et entraînement du modèle
    model = create_model(input_shape=(1, 2))
    model.fit(
        X_train, y_train,
        epochs=10,
        batch_size=32,
        validation_data=(X_test, y_test)
    )
    
    # Sauvegarde du modèle et du scaler
    model.save('/model/accident_predictor.h5')
    joblib.dump(scaler, '/model/scaler.pkl')
    
    # Évaluation du modèle
    loss, accuracy = model.evaluate(X_test, y_test)
    print(f"Test accuracy: {accuracy:.4f}")

if __name__ == "__main__":
    train_and_save_model() 