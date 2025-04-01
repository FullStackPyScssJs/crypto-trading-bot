import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
import logging

# 🔧 Ścieżki
BASE_DIR = "D:/TitanFlow/data/data"
DATA_DIR = os.path.join(BASE_DIR, "datasets")
MODEL_PATH = os.path.join(BASE_DIR, "model/lstm_best_model.h5")

# 🔧 Parametry modelu
SEQUENCE_LENGTH = 100
TP_SL_MULTIPLIER = 2  # Mnożnik ATR dla obliczeń TP/SL

# ✅ Wczytaj model
logging.info("🔄 Wczytywanie modelu...")
model = load_model(MODEL_PATH)

# ✅ Wczytaj dane do predykcji dla danego pliku
def load_latest_data(file_path):
    df = pd.read_csv(file_path)

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)

    required_columns = [
        "close", "volume", "SMA_50", "SMA_200", "VWAP", "ATR", "BB_middle",
        "BB_std", "BB_upper", "BB_lower", "RSI", "EMA_12", "EMA_26", "MACD",
        "MACD_signal", "profit_signal"
    ]

    # ✅ Jeśli brakuje `profit_signal`, dodaj jako 0
    if "profit_signal" not in df.columns:
        df["profit_signal"] = 0

    df = df[required_columns].fillna(method='bfill').fillna(method='ffill')  # Uzupełniamy braki

    return df[-SEQUENCE_LENGTH:]

# ✅ Skalowanie danych
def scale_data(df):
    scalers = {}

    for col in df.columns:
        scaler = MinMaxScaler(feature_range=(0, 1))
        df[col] = scaler.fit_transform(df[col].values.reshape(-1, 1))  # Dopasowanie i transformacja
        scalers[col] = scaler

    return df, scalers

# ✅ Predykcja dla pojedynczego tokena z obliczaniem TP i SL
def make_prediction(file_path):
    try:
        latest_data = load_latest_data(file_path)
        latest_data, scalers = scale_data(latest_data)

        X_input = np.array([latest_data.values])  # Tworzymy batch 1x100xN
        lstm_predictions = model.predict(X_input)

        # ✅ Spłaszczamy tablicę, aby uniknąć błędu wymiaru
        predicted_price = scalers["close"].inverse_transform([[lstm_predictions[0].flatten()[0]]])[0][0]
        predicted_trend = "Bullish" if lstm_predictions[1].flatten()[0] > 0.5 else "Bearish"
        predicted_volume = scalers["volume"].inverse_transform([[lstm_predictions[2].flatten()[0]]])[0][0]
        predicted_volatility = scalers["ATR"].inverse_transform([[lstm_predictions[3].flatten()[0]]])[0][0]
        buy_signal = "BUY" if lstm_predictions[4].flatten()[0] > 0.5 else "SELL"

        # ✅ Obliczanie TP i SL
        atr_value = predicted_volatility  # ATR to zmienność, której już używamy
        tp = predicted_price + TP_SL_MULTIPLIER * atr_value  # TP = Cena + 2 * ATR
        sl = predicted_price - TP_SL_MULTIPLIER * atr_value  # SL = Cena - 2 * ATR

        return {
            "price": predicted_price,
            "trend": predicted_trend,
            "volume": predicted_volume,
            "volatility": predicted_volatility,
            "signal": buy_signal,
            "tp": tp,
            "sl": sl
        }

    except Exception as e:
        logging.warning(f"⚠️ Błąd predykcji dla {file_path}: {e}")
        return None

# ✅ Przeprowadź predykcję dla wszystkich tokenów
def predict_all_tokens():
    lstm_predictions = {}

    for file in os.listdir(DATA_DIR):
        if file.endswith(".csv"):
            file_path = os.path.join(DATA_DIR, file)
            token = file.replace("_USDT.csv", "")
            prediction = make_prediction(file_path)

            if prediction:
                lstm_predictions[token] = prediction
                print(f"\n🔷 **{token}**\n"
                      f"💰 Cena: {prediction['price']:.2f} USDT\n"
                      f"📈 Trend: {prediction['trend']}\n"
                      f"📊 Wolumen: {prediction['volume']:.2f}\n"
                      f"📉 Zmienność: {prediction['volatility']:.4f}\n"
                      f"📢 Sygnał: {prediction['signal']}\n"
                      f"🚀 TP: {prediction['tp']:.2f}\n"
                      f"🛑 SL: {prediction['sl']:.2f}")

    return lstm_predictions

if __name__ == "__main__":
    print("\n🚀 **Rozpoczynam predykcję dla wszystkich tokenów...**")
    predictions = predict_all_tokens()

