import requests
import os
from dotenv import load_dotenv

load_dotenv()

public_node_url = os.getenv("PUBLIC_NODE_URL")


# Get price ratio between two tokens,
# token = the token price compared to luna
# e.g. "bluna" is 1 LUNA = 0.9 BLUNA returns 0.9
# e.g. "ust" is 1 LUNA = 30 UST returns 30
def get_ratio(token: str):
    value = 0
    bluna = luna = ust = None
    query_msg = '{"pool":{}}'

    luna_ust_pair_address = os.getenv("LUNA_UST_PAIR_ADDRESS")
    luna_bluna_pair_address = os.getenv("LUNA_BLUNA_PAIR_ADDRESS")

    # Luna to BLuna
    if token.lower() == "bluna":
        contract_address = luna_bluna_pair_address
    # Luna to UST
    elif token.lower() == "ust":
        contract_address = luna_ust_pair_address

    response = requests.get(
        public_node_url + "/wasm/contracts/" + contract_address + "/store",
        params={"query_msg": query_msg},
    ).json()

    response_array = response["result"]["assets"]

    # Iterate through the results to parse out the amount of a token in the contract
    for i in response_array:
        # If token is used instead of native_token then it is bluna
        if "token" in i["info"]:
            bluna = float(i["amount"])
        elif i["info"]["native_token"]["denom"] == "uluna":
            luna = float(i["amount"])
        else:
            ust = float(i["amount"])

    # If bluna and luna are both set then we can calculate the ratio
    if bluna and luna:
        value = luna / bluna
    # Else if Luna and UST are both set then we can calculate the ratio
    elif luna and ust:
        value = ust / luna

    return value


def get_balance(account_address: str, token: str):
    bluna_contract = os.getenv("BLUNA_CONTRACT")
    denominator = 1000000
    value = 0

    # If checking a native token then we can just pull the bank balance of the account
    if token == "uluna" or token == "uusd":
        response = requests.get(public_node_url + "/bank/balances/" + account_address)

    # When checking a contract token like bluna you need to check the contract for the balance of the account
    if token == "bluna":
        query_msg = '{"balance":{"address":"' + account_address + '"}}'
        response = requests.get(
            public_node_url + "/wasm/contracts/" + bluna_contract + "/store",
            params={"query_msg": query_msg},
        )

    # If the response was sucessful then we can parse out the balance
    if response.status_code == 200:
        results = response.json()["result"]
        # Bank balance returns all your native token balances so we need to grab the ones we are interested in
        if token == "uluna" or token == "uusd":
            for result in results:
                if result["denom"] == token:
                    value = float(result["amount"]) / denominator

        # When checking a contract token like bluna it only returns the balance of that token
        if token == "bluna":
            value = float(results["balance"]) / denominator

    return value
