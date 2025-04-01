import polars as pl
import asyncio

class TechnicalIndicators:
    """
    A class to calculate technical indicators for financial data.
    """

    @staticmethod
    async def calculate_sma(data, window):
        """
        Calculates Simple Moving Average (SMA).

        Args:
            data (pl.Series): The price series.
            window (int): The window size for SMA.

        Returns:
            pl.Series: The SMA values.
        """
        return data.rolling_mean(window)

    @staticmethod
    async def calculate_ema(data, window):
        """
        Calculates Exponential Moving Average (EMA).

        Args:
            data (pl.Series): The price series.
            window (int): The window size for EMA.

        Returns:
            pl.Series: The EMA values.
        """
        alpha = 2 / (window + 1)
        return data.ewm_mean(span=window, alpha=alpha)

    @staticmethod
    async def calculate_rsi(data, window):
        """
        Calculates Relative Strength Index (RSI).

        Args:
            data (pl.Series): The price series.
            window (int): The window size for RSI.

        Returns:
            pl.Series: The RSI values.
        """
        delta = data.diff()
        gain = delta.apply(lambda x: x if x > 0 else 0).rolling_mean(window)
        loss = (-delta).apply(lambda x: x if x > 0 else 0).rolling_mean(window)
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    async def calculate_macd(data, fast_window=12, slow_window=26, signal_window=9):
        """
        Calculates Moving Average Convergence Divergence (MACD).

        Args:
            data (pl.Series): The price series.
            fast_window (int): The fast EMA window size.
            slow_window (int): The slow EMA window size.
            signal_window (int): The signal line EMA window size.

        Returns:
            dict: A dictionary with MACD line and signal line.
        """
        fast_ema = await TechnicalIndicators.calculate_ema(data, fast_window)
        slow_ema = await TechnicalIndicators.calculate_ema(data, slow_window)
        macd_line = fast_ema - slow_ema
        signal_line = await TechnicalIndicators.calculate_ema(macd_line, signal_window)
        return {"MACD": macd_line, "Signal": signal_line}

    @staticmethod
    async def calculate_mfi(high, low, close, volume, window=14):
        """
        Calculates Money Flow Index (MFI).

        Args:
            high (pl.Series): High prices.
            low (pl.Series): Low prices.
            close (pl.Series): Close prices.
            volume (pl.Series): Volumes.
            window (int): The window size for MFI.

        Returns:
            pl.Series: The MFI values.
        """
        typical_price = (high + low + close) / 3
        money_flow = typical_price * volume
        positive_flow = (
            pl.when(typical_price.diff() > 0).then(money_flow).otherwise(0).rolling_sum(window)
        )
        negative_flow = (
            pl.when(typical_price.diff() <= 0).then(money_flow).otherwise(0).rolling_sum(window)
        )
        mfi = 100 - (100 / (1 + (positive_flow / negative_flow)))
        return mfi

    @staticmethod
    async def calculate_momentum(data, window):
        """
        Calculates Momentum.

        Args:
            data (pl.Series): The price series.
            window (int): The window size for Momentum.

        Returns:
            pl.Series: The Momentum values.
        """
        return data - data.shift(window)

    @staticmethod
    async def calculate_atr(high, low, close, window):
        """
        Calculates Average True Range (ATR).

        Args:
            high (pl.Series): High prices.
            low (pl.Series): Low prices.
            close (pl.Series): Close prices.
            window (int): The window size for ATR.

        Returns:
            pl.Series: The ATR values.
        """
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pl.concat([tr1, tr2, tr3], how="vertical").max(axis=1)
        return tr.rolling_mean(window)

    @staticmethod
    async def calculate_bollinger_bands(data, window, num_std_dev):
        """
        Calculates Bollinger Bands.

        Args:
            data (pl.Series): The price series.
            window (int): The window size for the moving average.
            num_std_dev (int): The number of standard deviations for the bands.

        Returns:
            dict: A dictionary with upper, middle, and lower bands.
        """
        sma = await TechnicalIndicators.calculate_sma(data, window)
        std_dev = data.rolling_std(window)
        upper_band = sma + (std_dev * num_std_dev)
        lower_band = sma - (std_dev * num_std_dev)
        return {"Upper Band": upper_band, "Middle Band": sma, "Lower Band": lower_band}
