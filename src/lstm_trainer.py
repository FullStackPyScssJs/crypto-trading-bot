import os
import logging
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import load_model, Model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt

# 🔧 Ścieżki
BASE_DIR = "D:/TitanFlow/data/data"
DATA_DIR = os.path.join(BASE_DIR, "datasets")
MODEL_DIR = os.path.join(BASE_DIR, "model")
LOG_DIR = os.path.join(BASE_DIR, "logs")

MODEL_PATH = os.path.join(MODEL_DIR, "lstm_best_model.h5")  # Istniejący model
LOG_FILE = os.path.join(LOG_DIR, "fine_tuning.log")
LOSS_PLOT = os.path.join(LOG_DIR, "fine_tuning_loss_plot.png")

# 🔧 Tworzenie folderów jeśli nie istnieją
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# 🔧 Konfiguracja logowania
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    encoding="utf-8"
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(message)s")
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

# 🔧 Hiperparametry
SEQUENCE_LENGTH = 100
BATCH_SIZE = 64
EPOCHS = 100  # Mniejsza liczba epok, bo to fine-tuning

class LSTMTrainer:
    def __init__(self, data_dir, model_save_path):
        self.data_dir = os.path.abspath(data_dir)
        self.model_save_path = os.path.abspath(model_save_path)
        self.scalers = {}

        # Wymagane kolumny w danych (16 cech)
        self.required_columns = [
            "close", "volume", "SMA_50", "SMA_200", "VWAP", "ATR", "BB_middle",
            "BB_std", "BB_upper", "BB_lower", "RSI", "EMA_12", "EMA_26", "MACD",
            "MACD_signal", "profit_signal"  # 16 cech
        ]

    def load_data(self):
        all_data = []
        for file in os.listdir(self.data_dir):
            file_path = os.path.join(self.data_dir, file)
            if file.endswith(".csv") and os.path.isfile(file_path):
                df = pd.read_csv(file_path)
                if "timestamp" in df.columns:
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                    df.set_index("timestamp", inplace=True)

                # Sprawdź, czy kolumna 'profit_signal' istnieje
                if "profit_signal" not in df.columns:
                    logging.warning(f"⚠️ Kolumna 'profit_signal' nie istnieje w pliku {file}. Dodaję ją...")
                    df['profit_signal'] = (df['close'].shift(-5) > df['close'] * 1.03).astype(int)

                # Upewnij się, że mamy tylko 16 cech
                df = df[self.required_columns]
                df.fillna(df.median(), inplace=True)

                # Dynamiczne TP i SL na podstawie ATR
                take_profit = df['close'] + 2 * df['ATR']  # TP = cena zamknięcia + 2 * ATR
                stop_loss = df['close'] - 2 * df['ATR']    # SL = cena zamknięcia - 2 * ATR

                if df.isnull().sum().sum() == 0:
                    all_data.append((df.values, take_profit.values, stop_loss.values))
                    logging.info(f"✅ Wczytano plik: {file} ({len(df)} wierszy)")

        if not all_data:
            raise ValueError("❌ Brak danych do trenowania!")

        # Połącz dane
        data = np.concatenate([d[0] for d in all_data])
        take_profit = np.concatenate([d[1] for d in all_data])
        stop_loss = np.concatenate([d[2] for d in all_data])

        # Normalizacja danych
        for i, col in enumerate(self.required_columns):
            self.scalers[col] = MinMaxScaler(feature_range=(0, 1))
            data[:, i] = self.scalers[col].fit_transform(data[:, i].reshape(-1, 1)).flatten()

        # Dodaj TP i SL do danych wyjściowych
        self.scalers['take_profit'] = MinMaxScaler(feature_range=(0, 1))
        self.scalers['stop_loss'] = MinMaxScaler(feature_range=(0, 1))
        take_profit = self.scalers['take_profit'].fit_transform(take_profit.reshape(-1, 1)).flatten()
        stop_loss = self.scalers['stop_loss'].fit_transform(stop_loss.reshape(-1, 1)).flatten()

        return data, take_profit, stop_loss

    def create_sequences(self, data, take_profit, stop_loss):
        X, y_price, y_trend, y_volume, y_volatility, y_profit_signal, y_tp, y_sl = [], [], [], [], [], [], [], []

        for i in range(len(data) - SEQUENCE_LENGTH - 1):
            X.append(data[i:i + SEQUENCE_LENGTH])
            y_price.append(data[i + SEQUENCE_LENGTH, 0])
            y_trend.append(1 if data[i + SEQUENCE_LENGTH, 0] > data[i + SEQUENCE_LENGTH - 1, 0] else 0)
            y_volume.append(data[i + SEQUENCE_LENGTH, 1])
            y_volatility.append(data[i + SEQUENCE_LENGTH, 5])
            y_profit_signal.append(data[i + SEQUENCE_LENGTH, -1])  # profit_signal
            y_tp.append(take_profit[i + SEQUENCE_LENGTH])  # take_profit
            y_sl.append(stop_loss[i + SEQUENCE_LENGTH])  # stop_loss

        return map(np.array, [X, y_price, y_trend, y_volume, y_volatility, y_profit_signal, y_tp, y_sl])

    def build_model(self):
        # Wczytanie istniejącego modelu
        model = load_model(self.model_save_path)

        # Przebudowa modelu, aby miał 7 wyjść
        inputs = model.input
        x = model.layers[-2].output  # Ostatnia warstwa przed wyjściami

        # Nowe warstwy wyjściowe z unikalnymi nazwami
        price_output = Dense(1, name="new_price_output")(x)
        trend_output = Dense(1, activation="sigmoid", name="new_trend_output")(x)
        volume_output = Dense(1, name="new_volume_output")(x)
        volatility_output = Dense(1, name="new_volatility_output")(x)
        profit_signal = Dense(1, activation="sigmoid", name="new_profit_signal")(x)
        tp_output = Dense(1, name="new_tp_output")(x)
        sl_output = Dense(1, name="new_sl_output")(x)

        # Nowy model z 7 wyjściami
        new_model = Model(inputs, outputs=[price_output, trend_output, volume_output, volatility_output, profit_signal, tp_output, sl_output])
        logging.info("✅ Przebudowano model z 7 wyjściami.")
        return new_model

    def train_model(self):
        logging.info("📊 Ładowanie danych...")
        data, take_profit, stop_loss = self.load_data()
        X, y_price, y_trend, y_volume, y_volatility, y_profit_signal, y_tp, y_sl = self.create_sequences(data, take_profit, stop_loss)

        # Wczytanie i kompilacja modelu
        model = self.build_model()
        optimizer = tf.keras.optimizers.Adam(learning_rate=0.0001)  # Mniejszy learning rate dla fine-tuningu
        model.compile(optimizer=optimizer, loss={
            "new_price_output": "mse",
            "new_trend_output": "binary_crossentropy",
            "new_volume_output": "mse",
            "new_volatility_output": "mse",
            "new_profit_signal": "binary_crossentropy",
            "new_tp_output": "mse",
            "new_sl_output": "mse"
        })

        # Callbacki
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6),
            ModelCheckpoint(self.model_save_path, save_best_only=True)
        ]

        # Trenowanie modelu
        logging.info("🔧 Rozpoczęcie fine-tuningu modelu...")
        history = model.fit(
            X, (y_price, y_trend, y_volume, y_volatility, y_profit_signal, y_tp, y_sl),  # Cele jako krotka
            epochs=EPOCHS,
            batch_size=BATCH_SIZE,
            validation_split=0.2,
            callbacks=callbacks
        )

        logging.info(f"✅ Model dotrenowany i zapisany do {self.model_save_path}")

        # Wykres strat
        plt.plot(history.history['loss'], label='train_loss')
        plt.plot(history.history['val_loss'], label='val_loss')
        plt.title('Fine-tuning Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        plt.savefig(LOSS_PLOT)
        plt.close()


if __name__ == "__main__":
    trainer = LSTMTrainer(DATA_DIR, MODEL_PATH)
    trainer.train_model()