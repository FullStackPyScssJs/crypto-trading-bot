import os
import logging
import pandas as pd
import requests
import time

ALCHEMY_API_KEY = "Youre API KEY"
ETHERSCAN_API_KEY = "Youre API KEY"
ONEINCH_API_KEY = "Youre API KEY"

DATA_DIR = "D:/TitanFlow/data/data/datasets"

TOKEN_CONTRACTS = {
    "ETH": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    "MATIC": "0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0",
    "LINK": "0x514910771af9ca656af840dff83e8264ec986ca",
    "DOT": None,
    "ADA": None,
    "XRP": None,
    "SOL": None
}

def fetch_tx_count(token_address):
    if not token_address:
        return 0
    url = f"https://eth-mainnet.alchemyapi.io/v2/{ALCHEMY_API_KEY}"
    payload = {
        "jsonrpc": "2.0",
        "method": "alchemy_getAssetTransfers",
        "params": [{"toAddress": token_address, "category": ["erc20"], "fromBlock": "latest"}],
        "id": 1
    }
    try:
        response = requests.post(url, json=payload).json()
        return len(response.get("result", []))
    except Exception as e:
        logging.warning(f"⚠️ Błąd pobierania tx_count dla {token_address}: {e}")
        return 0

def fetch_total_supply(token_address):
    if not token_address:
        return 0
    url = f"https://api.etherscan.io/api?module=stats&action=tokensupply&contractaddress={token_address}&apikey={ETHERSCAN_API_KEY}"
    try:
        response = requests.get(url).json()
        return int(response["result"]) / 10 ** 18 if "result" in response else 0
    except Exception as e:
        logging.warning(f"⚠️ Błąd pobierania total_supply dla {token_address}: {e}")
        return 0

def fetch_fear_greed_index():
    url = "https://api.alternative.me/fng/"
    try:
        response = requests.get(url).json()
        return float(response["data"][0]["value"]) if "data" in response else 0
    except Exception as e:
        logging.warning(f"⚠️ Błąd pobierania Fear & Greed Index: {e}")
        return 0

def fetch_1inch_data(token_symbol):
    token_address = TOKEN_CONTRACTS.get(token_symbol, None)
    if not token_address:
        return {"liquidity_depth": 0, "bid_ask_spread": 0}

    url = f"https://api.1inch.io/v5.0/1/liquiditySources?tokenAddress={token_address}"
    try:
        response = requests.get(url).json()
        if "protocols" in response:
            liquidity = sum(float(source.get("liquidity", 0)) for source in response["protocols"])
            bid_ask_spread = abs(float(response.get("bestSellPrice", 0)) - float(response.get("bestBuyPrice", 0)))
            return {"liquidity_depth": liquidity, "bid_ask_spread": bid_ask_spread}
    except Exception as e:
        logging.warning(f"⚠️ Błąd pobierania 1inch dla {token_symbol}: {e}")
    return {"liquidity_depth": 0, "bid_ask_spread": 0}

def update_dataset(file):
    file_path = os.path.join(DATA_DIR, file)
    token_symbol = file.split("_")[0]
    token_address = TOKEN_CONTRACTS.get(token_symbol, None)

    if not os.path.isfile(file_path):
        return

    df = pd.read_csv(file_path)
    logging.info(f"🔄 Aktualizowanie danych dla {file}...")

    df["tx_count"].fillna(fetch_tx_count(token_address), inplace=True)
    df["total_supply"].fillna(fetch_total_supply(token_address), inplace=True)
    df["fear_greed_index"].fillna(fetch_fear_greed_index(), inplace=True)

    if "liquidity_depth" not in df.columns:
        df["liquidity_depth"] = 0
    if "bid_ask_spread" not in df.columns:
        df["bid_ask_spread"] = 0

    liquidity_data = fetch_1inch_data(token_symbol)
    df["liquidity_depth"].fillna(liquidity_data["liquidity_depth"], inplace=True)
    df["bid_ask_spread"].fillna(liquidity_data["bid_ask_spread"], inplace=True)

    df.fillna(0, inplace=True)

    df.to_csv(file_path, index=False)
    logging.info(f"✅ Plik {file} zaktualizowany!")

def update_all_datasets():
    for file in os.listdir(DATA_DIR):
        if file.endswith(".csv"):
            update_dataset(file)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    update_all_datasets()