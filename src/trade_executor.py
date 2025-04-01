# trade_executor.py
import logging
import ccxt
from lstm_predictor import make_prediction  # Zmiana importu
from data_fetcher import DataFetcher

class TradeExecutor:
    def __init__(self, config):
        """
        Initializes the TradeExecutor with configuration parameters.

        Args:
            config (dict): The bot's configuration for trading execution.
        """
        self.trade_config = config
        self.api_key = config.get("exchange", {}).get("api_key")
        self.api_secret = config.get("exchange", {}).get("api_secret")
        self.exchange_name = config.get("exchange", {}).get("name", "bybit")
        self.exchange_mode = config.get("exchange", {}).get("exchange_mode", "mainnet")

        try:
            # Initialize exchange with testnet or mainnet endpoint
            exchange_class = getattr(ccxt, self.exchange_name)
            if self.exchange_mode == "testnet":
                self.exchange = exchange_class({
                    "apiKey": self.api_key,
                    "secret": self.api_secret,
                    "enableRateLimit": True,
                    "urls": {
                        "api": "https://api-testnet.bybit.com"  # Testnet URL for Bybit
                    }
                })
            else:
                self.exchange = exchange_class({
                    "apiKey": self.api_key,
                    "secret": self.api_secret,
                    "enableRateLimit": True
                })

            logging.info(f"Initialized exchange: {self.exchange_name} ({self.exchange_mode})")
        except Exception as init_err:
            logging.error(f"Failed to initialize exchange: {init_err}")
            raise

        # Initialize Data Fetcher
        self.data_fetcher = DataFetcher()

    def execute_trade(self, symbol, side, amount, price=None):
        """
        Executes a trade on the configured exchange with dynamic SL/TP adjustments.

        Args:
            symbol (str): The trading pair (e.g., "BTC/USDT").
            side (str): "buy" or "sell".
            amount (float): The amount to trade.
            price (float, optional): The price for a limit order. Defaults to None.

        Returns:
            dict: The response from the exchange.
        """
        try:
            # Fetch real-time market data
            market_data = self.data_fetcher.get_data_for_model(symbol)

            # Predict optimal SL/TP percentages using LSTM
            predictions = make_prediction(symbol)  # Używamy funkcji make_prediction
            if not predictions:
                logging.warning("No predictions available. Skipping trade.")
                return {}

            sl_percent = predictions.get("stop_loss", self.trade_config["risk_management"].get("default_stop_loss", 5))
            tp_percent = predictions.get("take_profit", self.trade_config["risk_management"].get("default_take_profit", 12))

            logging.info(f"Dynamic SL: {sl_percent}%, TP: {tp_percent}% for {symbol}")

            if price:
                # Limit order
                order = self.exchange.create_limit_order(symbol, side, amount, price)
            else:
                # Market order
                order = self.exchange.create_market_order(symbol, side, amount)

            logging.info(f"Trade executed: {order}")
            return order

        except ccxt.NetworkError as network_err:
            logging.error(f"Network error during trade execution: {network_err}")
        except ccxt.ExchangeError as exchange_err:
            logging.error(f"Exchange error during trade execution: {exchange_err}")
        except Exception as unexpected_err:
            logging.error(f"Unexpected error during trade execution: {unexpected_err}")

        return {}

    def fetch_balance(self):
        """
        Fetches the account balance from the exchange.

        Returns:
            dict: The balance data.
        """
        try:
            balance_data = self.exchange.fetch_balance()
            logging.info("Fetched account balance successfully.")
            return balance_data
        except ccxt.NetworkError as network_err:
            logging.error(f"Network error during balance fetch: {network_err}")
        except ccxt.ExchangeError as exchange_err:
            logging.error(f"Exchange error during balance fetch: {exchange_err}")
        except Exception as unexpected_err:
            logging.error(f"Unexpected error during balance fetch: {unexpected_err}")

        return {}

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Example configuration
    trade_config = {
        "exchange": {
            "name": "bybit",
            "api_key": "your_testnet_api_key",
            "api_secret": "your_testnet_api_secret",
            "exchange_mode": "testnet"  # Set to "testnet" or "mainnet"
        },
        "risk_management": {
            "default_stop_loss": 5,
            "default_take_profit": 12
        }
    }

    executor = TradeExecutor(trade_config)

    # Example trade
    try:
        trade_response = executor.execute_trade("BTC/USDT", "buy", 0.001)
        print(trade_response)

        # Example balance fetch
        account_balance = executor.fetch_balance()
        print(account_balance)
    except Exception as main_err:
        logging.error(f"Error in trade execution or balance fetch: {main_err}")
