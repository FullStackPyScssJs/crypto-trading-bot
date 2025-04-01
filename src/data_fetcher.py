import asyncio
import logging
import ccxt
import os
import pandas as pd
import numpy as np

class DataFetcher:
    def __init__(self):
        """
        Initializes the DataFetcher without requiring API keys.
        """
        self.exchange = self._initialize_exchange()

    @staticmethod
    def _initialize_exchange():
        """
        Initializes the exchange instance using ccxt.

        Returns:
            ccxt.Exchange: An instance of the ccxt exchange.
        """
        try:
            exchange = ccxt.bybit({
                'options': {
                    'defaultType': 'spot',  # Default to spot markets
                },
            })
            logging.info("Exchange initialized successfully.")
            return exchange
        except Exception as init_error:
            logging.error(f"Error initializing exchange: {init_error}")
            raise

    async def fetch_markets(self):
        """
        Fetches all available markets and filters for USDT pairs.

        Returns:
            list: A list of symbols trading against USDT.
        """
        try:
            markets = await asyncio.to_thread(self.exchange.fetch_markets)
            usdt_pairs = [market['symbol'] for market in markets if market['quote'] == 'USDT']
            logging.info(f"Fetched {len(usdt_pairs)} USDT pairs.")
            return usdt_pairs
        except Exception as e:
            logging.error(f"Error fetching markets: {e}")
            return []

    async def fetch_ohlcv(self, symbol, timeframe='1d', limit=100):
        """
        Fetches historical OHLCV data for the specified symbol.

        Args:
            symbol (str): The trading pair symbol (e.g., 'BTC/USDT').
            timeframe (str): The time frame for the data (default '1d').
            limit (int): The number of data points to fetch (default 100).

        Returns:
            list: A list of OHLCV data.
        """
        try:
            ohlcv = await asyncio.to_thread(self.exchange.fetch_ohlcv, symbol, timeframe, limit=limit)
            logging.info(f"Fetched {len(ohlcv)} OHLCV data points for {symbol}.")
            return ohlcv
        except Exception as e:
            logging.error(f"Error fetching OHLCV data for {symbol}: {e}")
            return []

    @staticmethod
    def calculate_rsi(ohlcv_data, window=14):
        """Calculate Relative Strength Index (RSI)."""
        df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]  # Return the last RSI value

    def calculate_ema(self, ohlcv_data, period):
        """Calculate Exponential Moving Average (EMA)."""
        df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        ema = df['close'].ewm(span=period, adjust=False).mean()
        return ema.iloc[-1]

    def calculate_sma(self, ohlcv_data, window):
        """Calculate Simple Moving Average (SMA)."""
        df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        sma = df['close'].rolling(window=window).mean()
        return sma.iloc[-1]

    def calculate_vwap(self, ohlcv_data):
        """Calculate Volume Weighted Average Price (VWAP)."""
        df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        vwap = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
        return vwap.iloc[-1]

    def calculate_atr(self, ohlcv_data, window=14):
        """Calculate Average True Range (ATR)."""
        df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['high-low'] = df['high'] - df['low']
        df['high-close'] = (df['high'] - df['close'].shift()).abs()
        df['low-close'] = (df['low'] - df['close'].shift()).abs()
        df['true_range'] = df[['high-low', 'high-close', 'low-close']].max(axis=1)
        atr = df['true_range'].rolling(window=window).mean()
        return atr.iloc[-1]

    def calculate_bollinger_bands(self, ohlcv_data, window=20, num_std=2):
        """Calculate Bollinger Bands (BB)."""
        df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        sma = df['close'].rolling(window=window).mean()
        std = df['close'].rolling(window=window).std()
        bb_middle = sma.iloc[-1]
        bb_upper = (sma + (std * num_std)).iloc[-1]
        bb_lower = (sma - (std * num_std)).iloc[-1]
        return bb_middle, bb_upper, bb_lower

    def calculate_macd(self, ohlcv_data, short_window=12, long_window=26, signal_window=9):
        """Calculate Moving Average Convergence Divergence (MACD)."""
        df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        short_ema = df['close'].ewm(span=short_window, adjust=False).mean()
        long_ema = df['close'].ewm(span=long_window, adjust=False).mean()
        macd = short_ema - long_ema
        macd_signal = macd.ewm(span=signal_window, adjust=False).mean()
        return macd.iloc[-1], macd_signal.iloc[-1]

    async def get_data_for_model(self, symbol, timeframe='1d', limit=200):  # Zwiększamy limit do 200
        # Fetch OHLCV data (pobieramy dane dla ostatnich 200 dni)
        ohlcv = await self.fetch_ohlcv(symbol, timeframe, limit=limit)

        if ohlcv:
            # Calculate all indicators
            sma_50 = self.calculate_sma(ohlcv, 50)
            sma_200 = self.calculate_sma(ohlcv, 200)  # SMA 200 z danych dla 200 dni
            vwap = self.calculate_vwap(ohlcv)
            atr = self.calculate_atr(ohlcv)
            bb_middle, bb_upper, bb_lower = self.calculate_bollinger_bands(ohlcv)
            rsi = self.calculate_rsi(ohlcv)
            ema_12 = self.calculate_ema(ohlcv, 12)
            ema_26 = self.calculate_ema(ohlcv, 26)
            macd, macd_signal = self.calculate_macd(ohlcv)

            # Prepare data in the required format for the model
            data = {
                "timestamp": [pd.to_datetime(entry[0], unit='ms').strftime('%Y-%m-%d') for entry in ohlcv],
                # Convert and format timestamp
                "open": [entry[1] for entry in ohlcv],
                "high": [entry[2] for entry in ohlcv],
                "low": [entry[3] for entry in ohlcv],
                "close": [entry[4] for entry in ohlcv],
                "volume": [entry[5] for entry in ohlcv],
                "SMA_50": [sma_50] * len(ohlcv),
                "SMA_200": [sma_200] * len(ohlcv),  # Teraz mamy dane dla SMA 200
                "VWAP": [vwap] * len(ohlcv),
                "ATR": [atr] * len(ohlcv),
                "BB_middle": [bb_middle] * len(ohlcv),
                "BB_upper": [bb_upper] * len(ohlcv),
                "BB_lower": [bb_lower] * len(ohlcv),
                "RSI": [rsi] * len(ohlcv),
                "EMA_12": [ema_12] * len(ohlcv),
                "EMA_26": [ema_26] * len(ohlcv),
                "MACD": [macd] * len(ohlcv),
                "MACD_signal": [macd_signal] * len(ohlcv)
            }

            # Convert data to DataFrame
            df = pd.DataFrame(data)

            # Ensure the directory exists
            output_dir = 'D:/TitanFlow/data/live_data'
            os.makedirs(output_dir, exist_ok=True)

            # Save the DataFrame to CSV
            file_path = os.path.join(output_dir, f"{symbol.replace('/', '')}_data.csv")
            df.to_csv(file_path, index=False)
            logging.info(f"Data saved to {file_path}")

            # Log the full data for verification
            logging.info(f"Data for {symbol}:")
            logging.info(df.tail())  # Print the last few rows of data for verification

            # Return data for the model
            return data
        return None

    async def monitor_markets(self, symbols):
        """
        Monitors multiple USDT pairs asynchronously.

        Args:
            symbols (list): List of trading pairs to monitor.
        """
        tasks = [self.get_data_for_model(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)
        for symbol, data in zip(symbols, results):
            if data:
                logging.info(f"Data for {symbol}: {data}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    data_fetcher = DataFetcher()

    async def main():
        # Fetch all USDT pairs
        usdt_pairs = await data_fetcher.fetch_markets()

        # Monitor the fetched USDT pairs
        if usdt_pairs:
            await data_fetcher.monitor_markets(usdt_pairs[:5])  # Limit to first 5 pairs for testing

    asyncio.run(main())
