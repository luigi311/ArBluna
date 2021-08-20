from scripts.send_notification import notify
from time import sleep
import requests
import os
from dotenv import load_dotenv

load_dotenv()

public_node_url = os.getenv("PUBLIC_NODE_URL")


def get_ratio(token: str):
    value = bluna = luna = ust = None
    query_msg = '{"pool":{}}'

    luna_ust_pair_address = os.getenv("LUNA_UST_PAIR_ADDRESS")
    luna_bluna_pair_address = os.getenv("LUNA_BLUNA_PAIR_ADDRESS")

    if token == "bluna":
        # Luna to Bluna
        contract_address = luna_bluna_pair_address
    elif token == "ust":
        # luna to Ust
        contract_address = luna_ust_pair_address

    response = requests.get(
        public_node_url + "/wasm/contracts/" + contract_address + "/store",
        params={"query_msg": query_msg},
    ).json()

    response_array = response["result"]["assets"]
    for i in response_array:
        if "token" in i["info"]:
            bluna = float(i["amount"])
        elif i["info"]["native_token"]["denom"] == "uluna":
            luna = float(i["amount"])
        else:
            ust = float(i["amount"])

    if bluna and luna:
        value = luna / bluna
    elif luna and ust:
        value = ust / luna

    if value is None:
        value = 0
    return value


def get_balance(wallet: str, token: str):
    bluna_contract = os.getenv("BLUNA_CONTRACT")
    denominator = 1000000

    if token == "uluna" or token == "uusd":
        response = requests.get(public_node_url + "/bank/balances/" + wallet)

    if token == "bluna":
        query_msg = '{"balance":{"address":"' + wallet + '"}}'
        response = requests.get(
            public_node_url + "/wasm/contracts/" + bluna_contract + "/store",
            params={"query_msg": query_msg},
        )

    value = None
    if response.status_code == 200:
        results = response.json()["result"]
        if token == "uluna" or token == "uusd":
            for result in results:
                if result["denom"] == token:
                    value = float(result["amount"]) / denominator

        if token == "bluna":
            value = float(results["balance"]) / denominator

    if value is None:
        value = 0

    return value


def get_balances(account_address: str):
    luna_balance = get_balance(account_address, "uluna")
    bluna_balance = get_balance(account_address, "bluna")
    ust_balance = get_balance(account_address, "uusd")

    notify(f"Balance: Luna {luna_balance} | Bluna {bluna_balance} | UST {ust_balance}")

    return [luna_balance, bluna_balance, ust_balance]
