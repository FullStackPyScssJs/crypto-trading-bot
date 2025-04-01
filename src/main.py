import asyncio
import logging
import polars as pl
from data_fetcher import DataFetcher
from strategy import TradingStrategy
from utils import TechnicalIndicators  # Dodajemy import klasy TechnicalIndicators

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)

async def main():
    # Inicjalizacja DataFetcher do pobierania danych z giełdy
    data_fetcher = DataFetcher()

    # Pobieranie dostępnych par USDT
    usdt_pairs = await data_fetcher.fetch_markets()
    if not usdt_pairs:
        logging.error("Nie udało się pobrać par USDT.")
        return

    # Ograniczenie do pierwszych 5 par dla testów
    usdt_pairs = usdt_pairs[:5]

    # Pobieranie danych OHLCV dla każdej pary
    ohlcv_data = {}
    for symbol in usdt_pairs:
        ohlcv = await data_fetcher.fetch_ohlcv(symbol)
        if ohlcv:
            ohlcv_data[symbol] = ohlcv

    # Konfiguracja strategii handlowej
    strategy_config = {
        "name": "rsi_macd",  # Można zmienić na inną strategię
        "rsi_window": 14,
        "bollinger_window": 20,
        "bollinger_std_dev": 2,
        "mfi_window": 14,
        "momentum_window": 14,
    }

    # Inicjalizacja strategii handlowej
    trading_strategy = TradingStrategy(strategy_config)

    # Parametry TP/SL
    TP_SL_MULTIPLIER = 2  # Mnożnik ATR dla TP/SL

    # Generowanie sygnałów handlowych i wyznaczanie TP/SL
    for symbol, ohlcv in ohlcv_data.items():
        # Tworzenie DataFrame z danych OHLCV
        price_data = pl.DataFrame({
            "timestamp": [x[0] for x in ohlcv],
            "open": [x[1] for x in ohlcv],
            "high": [x[2] for x in ohlcv],
            "low": [x[3] for x in ohlcv],
            "close": [x[4] for x in ohlcv],
            "volume": [x[5] for x in ohlcv],
        })

        # Obliczanie ATR (Average True Range) dla TP/SL
        atr = await TechnicalIndicators.calculate_atr(  # Używamy TechnicalIndicators zamiast TradingStrategy
            price_data["high"], price_data["low"], price_data["close"], window=14
        )

        # Ostatnia cena zamknięcia
        last_close = price_data["close"][-1]

        # Obliczanie TP i SL
        tp = last_close + TP_SL_MULTIPLIER * atr[-1]
        sl = last_close - TP_SL_MULTIPLIER * atr[-1]

        # Generowanie sygnałów handlowych
        signals = await trading_strategy.generate_signals(price_data)
        logging.info(f"Sygnały handlowe dla {symbol}: {signals}")
        logging.info(f"TP: {tp}, SL: {sl}")

if __name__ == "__main__":
    asyncio.run(main())