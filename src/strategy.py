import logging
import polars as pl
from utils import TechnicalIndicators

class TradingStrategy:
    """
    A class for implementing various trading strategies.
    """

    def __init__(self, strategy_configuration):
        """
        Initializes the TradingStrategy with configuration parameters.

        Args:
            strategy_configuration (dict): The bot's configuration.
        """
        self.strategy_config = strategy_configuration

    async def strategy_rsi_macd(self, price_data):
        """
        RSI + MACD strategy: Buy when RSI is oversold and MACD indicates upward trend.

        Args:
            price_data (pl.DataFrame): The input data.

        Returns:
            pl.DataFrame: Data with signals.
        """
        enriched_data = price_data.with_columns([
            (await TechnicalIndicators.calculate_rsi(price_data["close"], self.strategy_config["rsi_window"])).alias(
                "RSI"),
            (await TechnicalIndicators.calculate_macd(price_data["close"]))["MACD"].alias("MACD"),
            (await TechnicalIndicators.calculate_macd(price_data["close"]))["Signal"].alias("MACD_Signal"),
        ])

        enriched_data = enriched_data.with_columns([
            pl.when((enriched_data["RSI"] < 30) & (enriched_data["MACD"] > enriched_data["MACD_Signal"]))
            .then("BUY")
            .when((enriched_data["RSI"] > 70) & (enriched_data["MACD"] < enriched_data["MACD_Signal"]))
            .then("SELL")
            .otherwise("HOLD")
            .alias("Signal")
        ])

        return enriched_data

    async def strategy_bollinger_breakout(self, price_data):
        """
        Bollinger Bands breakout strategy.

        Args:
            price_data (pl.DataFrame): The input data.

        Returns:
            pl.DataFrame: Data with signals.
        """
        bollinger_data = await TechnicalIndicators.calculate_bollinger_bands(
            price_data["close"],
            self.strategy_config["bollinger_window"],
            self.strategy_config["bollinger_std_dev"]
        )

        enriched_data = price_data.with_columns([
            bollinger_data["Upper Band"].alias("Bollinger_Upper"),
            bollinger_data["Lower Band"].alias("Bollinger_Lower"),
        ])

        enriched_data = enriched_data.with_columns([
            pl.when(enriched_data["close"] < enriched_data["Bollinger_Lower"]).then("BUY")
            .when(enriched_data["close"] > enriched_data["Bollinger_Upper"]).then("SELL")
            .otherwise("HOLD")
            .alias("Signal")
        ])

        return enriched_data

    async def strategy_money_flow_momentum(self, price_data):
        """
        Money Flow Index (MFI) and Momentum strategy: Buy when MFI is oversold and Momentum is positive.

        Args:
            price_data (pl.DataFrame): The input data.

        Returns:
            pl.DataFrame: Data with signals.
        """
        enriched_data = price_data.with_columns([
            (await TechnicalIndicators.calculate_mfi(
                price_data["high"], price_data["low"], price_data["close"], price_data["volume"],
                self.strategy_config.get("mfi_window", 14)
            )).alias("MFI"),
            (await TechnicalIndicators.calculate_momentum(
                price_data["close"],
                self.strategy_config.get("momentum_window", 14)
            )).alias("Momentum"),
        ])

        enriched_data = enriched_data.with_columns([
            pl.when((enriched_data["MFI"] < 20) & (enriched_data["Momentum"] > 0)).then("BUY")
            .when((enriched_data["MFI"] > 80) & (enriched_data["Momentum"] < 0)).then("SELL")
            .otherwise("HOLD")
            .alias("Signal")
        ])

        return enriched_data

    async def generate_signals(self, price_data):
        """
        Selects and applies the chosen strategy to generate trading signals.

        Args:
            price_data (pl.DataFrame): The input data containing price information.

        Returns:
            pl.DataFrame: A DataFrame with generated trading signals.
        """
        strategy_name = self.strategy_config["name"]

        if strategy_name == "rsi_macd":
            return await self.strategy_rsi_macd(price_data)
        elif strategy_name == "bollinger_breakout":
            return await self.strategy_bollinger_breakout(price_data)
        elif strategy_name == "money_flow_momentum":
            return await self.strategy_money_flow_momentum(price_data)
        else:
            raise ValueError(f"Unknown strategy: {strategy_name}")

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Simulated configuration
    config = {
        "name": "money_flow_momentum",
        "rsi_window": 14,
        "bollinger_window": 20,
        "bollinger_std_dev": 2,
        "mfi_window": 14,
        "momentum_window": 14,
    }

    # Sample data
    market_data = pl.DataFrame({
        "open": [100, 101, 102, 103, 104],
        "high": [105, 106, 107, 108, 109],
        "low": [95, 96, 97, 98, 99],
        "close": [102, 103, 104, 105, 106],
        "volume": [1000, 1100, 1200, 1300, 1400],
    })

    strategy = TradingStrategy(config)

    # Run strategy asynchronously
    import asyncio
    signals = asyncio.run(strategy.generate_signals(market_data))
    print(signals)
