import requests
import os
from dotenv import load_dotenv

load_dotenv()

public_node_url = os.getenv("PUBLIC_NODE_URL")
denominator = 1000000

# Get price ratio between two tokens,
# token = the token price compared to luna
# e.g. "bluna" is 1 LUNA = 0.9 BLUNA returns 0.9
# e.g. "ust" is 1 LUNA = 30 UST returns 30
def get_ratio(to_token: str, amount: float):
    value = 0
    bluna = luna = ust = None

    if amount==0:
        amount = str(denominator)
    else:
        amount = str(int(amount*denominator))

    luna_ust_pair_address = os.getenv("LUNA_UST_PAIR_ADDRESS")
    luna_bluna_pair_address = os.getenv("LUNA_BLUNA_PAIR_ADDRESS")

    # Luna to BLuna
    if to_token.lower() == "bluna":
        contract_address = luna_bluna_pair_address
        query_msg = '{"simulation":{"offer_asset":{"amount":"'+ amount +'","info":{"native_token":{"denom":"uluna"}}}}}'

    # Bluna to Luna
    elif to_token.lower() == "luna":
        contract_address = luna_bluna_pair_address
        query_msg = '{"simulation":{"offer_asset":{"amount":"'+ amount +'","info":{"token":{"contract_addr":"terra1kc87mu460fwkqte29rquh4hc20m54fxwtsx7gp"}}}}}'


    # Luna to UST
    elif to_token.lower() == "ust":
        contract_address = luna_ust_pair_address
        query_msg = '{"simulation":{"offer_asset":{"amount":"'+ amount +'","info":{"native_token":{"denom":"uluna"}}}}}'


    response = requests.get(
        public_node_url + "/wasm/contracts/" + contract_address + "/store",
        params={"query_msg": query_msg},
    ).json()
    
    # Luna to BLuna
    if to_token.lower() == "bluna":
        luna = float(amount)
        bluna = float(response["result"]["return_amount"])
        value = bluna / luna
    
    # Bluna to Luna
    if to_token.lower() == "luna":
        luna = float(response["result"]["return_amount"])
        bluna = float(amount)
        value = luna / bluna

    # Luna to UST
    elif to_token.lower() == "ust":
        luna = float(amount)
        ust = float(response["result"]["return_amount"])
        value = ust / luna

    return value


def get_balance(account_address: str, token: str):
    bluna_contract = os.getenv("BLUNA_CONTRACT")
    
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
