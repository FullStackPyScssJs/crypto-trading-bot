import logging
import requests
import yaml
import os
import sys
from datetime import datetime, timedelta, timezone


class OnchainMonitor:
    def __init__(self, secrets_file=None):
        """
        Initializes the OnchainMonitor with configuration parameters.

        Args:
            secrets_file (str, optional): Path to the secrets.yaml file. Defaults to config/secrets.yaml.
        """
        if secrets_file is None:
            secrets_file = "D:/TitanFlow/config/secrets.yaml"

        self.secrets = self.load_secrets(secrets_file)
        self.santiment_api_key = self.secrets.get("santiment_api_key")
        self.etherscan_api_key = self.secrets.get("etherscan_api_key")
        self.alchemy_api_key = self.secrets.get("alchemy", {}).get("api_key")
        self.alchemy_base_url = self.secrets.get("alchemy", {}).get("api_url")

    @staticmethod
    def load_secrets(file_path):
        """
        Loads secrets from the specified YAML file.

        Args:
            file_path (str): Path to the secrets.yaml file.

        Returns:
            dict: Parsed YAML secrets.
        """
        try:
            with open(file_path, "r") as file:
                return yaml.safe_load(file)
        except Exception as error:
            logging.error(f"Error loading secrets file: {error} (Path: {file_path})")
            return {}

    def fetch_active_addresses_etherscan(self, monitored_token, past_days):
        """
        Fetches the unique active addresses for a token using Etherscan API.

        Args:
            monitored_token (str): The token to monitor.
            past_days (int): The number of past days to consider.

        Returns:
            dict: Active addresses data.
        """
        to_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        from_date = (datetime.now(timezone.utc) - timedelta(days=past_days)).strftime("%Y-%m-%dT%H:%M:%SZ")

        url = f"https://api.etherscan.io/api?module=account&action=txlist&address={monitored_token}&startblock=0&endblock=99999999&page=1&offset=100&sort=asc&apikey={self.etherscan_api_key}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            logging.info("Fetched active addresses data successfully from Etherscan.")
            return response.json()
        except requests.RequestException as error:
            logging.error(f"Error fetching active addresses from Etherscan: {error} | Response: {response.text if 'response' in locals() else 'No response'}")
            return {}

    def fetch_transactions_alchemy(self, monitored_token, past_days):
        """
        Fetches the token transactions from Alchemy API.

        Args:
            monitored_token (str): The token to monitor.
            past_days (int): The number of past days to consider.

        Returns:
            dict: Transactions data.
        """
        to_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        from_date = (datetime.now(timezone.utc) - timedelta(days=past_days)).strftime("%Y-%m-%dT%H:%M:%SZ")

        url = f"{self.alchemy_base_url}/v2/{self.alchemy_api_key}/get_asset_transfers"

        params = {
            "fromBlock": "0x0",
            "toBlock": "latest",
            "contractAddresses": [monitored_token],
            "category": ["erc20"],
            "maxCount": "1000"
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            logging.info("Fetched transactions data successfully from Alchemy.")
            return response.json()
        except requests.RequestException as error:
            logging.error(f"Error fetching transactions from Alchemy: {error} | Response: {response.text if 'response' in locals() else 'No response'}")
            return {}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    exit_code = 0

    try:
        monitor = OnchainMonitor(secrets_file="D:/TitanFlow/config/secrets.yaml")

        # Test fetching active addresses from Etherscan
        active_addresses_etherscan = monitor.fetch_active_addresses_etherscan("0x742d35Cc6634C0532925a3b844Bc454e4438f44e", 7)  # Example ETH address
        print(active_addresses_etherscan)

        # Test fetching transactions from Alchemy
        transactions_alchemy = monitor.fetch_transactions_alchemy("0x742d35Cc6634C0532925a3b844Bc454e4438f44e", 7)  # Example ETH address
        print(transactions_alchemy)

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        exit_code = 1

    sys.exit(exit_code)
