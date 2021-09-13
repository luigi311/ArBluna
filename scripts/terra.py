import os, requests, base64
from terra_sdk.client.lcd import LCDClient
from terra_sdk.key.mnemonic import MnemonicKey
from terra_sdk.core.coins import Coins
from terra_sdk.core.coins import Coin
from terra_sdk.core.auth import StdFee
from terra_sdk.core.wasm import MsgExecuteContract
from terra_sdk.exceptions import LCDResponseError
from scripts.send_notification import notify, notify_swap
from scripts.get_info import get_balance
from time import sleep
from dotenv import load_dotenv

load_dotenv(override=True)

chain_id = "columbus-4"

public_node_url = os.getenv("PUBLIC_NODE_URL")
mnemonic = os.getenv("MNEMONIC")
sleep_duration = float(os.getenv("SLEEP_DURATION"))
spread = float(os.getenv("MAX_SPREAD"))

denominator = 1000000

# Connect to Testnet
terra = LCDClient(chain_id=chain_id, url=public_node_url)
# Desire wallet via passphrase
mk = MnemonicKey(mnemonic=mnemonic)
# Define what wallet to use
wallet = terra.wallet(mk)
# Account Add
account_address = wallet.key.acc_address


def execute_swap(amount: float, to_token: str, price: float):
    # Convert token amount to amount needed by terra
    amount = int(amount * denominator)

    # Addresses needed to swap between the 3 assets
    luna_bluna_pair_address = os.getenv("LUNA_BLUNA_PAIR_ADDRESS")
    luna_ust_pair_address = os.getenv("LUNA_UST_PAIR_ADDRESS")
    bluna_contract = os.getenv("BLUNA_CONTRACT")

    # When swapping to bluna, create structure for native token to contract token swap
    # Must point to luna_bluna_pair_address, must provide the luna coins and specify the address that the bluna should go to
    if to_token == "bluna":
        coin = Coin("uluna", amount).to_data()
        coins = Coins.from_data([coin])
        send = (
            MsgExecuteContract(
                sender=account_address,
                contract=luna_bluna_pair_address,
                execute_msg={
                    "swap": {
                        "belief_price": str(price),
                        "max_spread": str(spread),
                        "offer_asset": {
                            "info": {"native_token": {"denom": "uluna"}},
                            "amount": str(int(amount)),
                        },
                        "to": account_address,
                    }
                },
                coins=coins,
            ),
        )
        sold_token = "luna"
    # When swapping to luna, create structure for contract token to native token swap
    # Must point to luna_bluna_pair_address, it will automatically pull in the bLuna coin and send the luna to the sender address
    elif to_token == "luna":
        encode_message = (
            '{"swap":{"belief_price": "'
            + str(price)
            + '","max_spread": "'
            + str(spread)
            + '"}}'
        )
        message_bytes = encode_message.encode("ascii")
        base64_message = base64.b64encode(message_bytes)
        send = (
            MsgExecuteContract(
                sender=account_address,
                contract=bluna_contract,
                execute_msg={
                    "send": {
                        "contract": luna_bluna_pair_address,
                        "amount": str(int(amount)),
                        "msg": str(base64_message)[2:-1],
                    }
                },
                coins=Coins(),
            ),
        )
        sold_token = "bluna"
    # When swapping to ust, create structure for native token to native token swap
    # Must point to luna_ust_pair_address, must provide the luna coins and send it will send the UST to the sender address
    elif to_token == "uusd":
        coin = Coin("uluna", amount).to_data()
        coins = Coins.from_data([coin])
        send = (
            MsgExecuteContract(
                sender=account_address,
                contract=luna_ust_pair_address,
                execute_msg={
                    "swap": {
                        "belief_price": str(price),
                        "max_spread": str(spread),
                        "offer_asset": {
                            "info": {"native_token": {"denom": "uluna"}},
                            "amount": str(int(amount)),
                        },
                    }
                },
                coins=coins,
            ),
        )
        sold_token = "luna"
    else:
        raise Exception(f"Invalid token {to_token}")

    # Get fee from terra fcd
    fees = requests.get(
        "https://fcd.terra.dev/v1/txs/gas_prices", timeout=sleep_duration
    ).json()
    fee = str(int(float(fees["uusd"]) * denominator)) + "uusd"
    memo_msg = "ArBluna - https://github.com/luigi311/ArBluna/tree/main"

    # Send transaction to execute contract
    sendtx = wallet.create_and_sign_tx(
        send, fee=StdFee(denominator, fee), memo=memo_msg
    )
    result = terra.tx.broadcast(sendtx)

    # Notify the user about the transaction
    notify_swap(amount / denominator, sold_token, price)

    return result.txhash


# Check the transaction status of the swap
# Source: https://github.com/unl1k3ly/AnchorHODL
def check_tx_info(tx_hash: str):
    try:
        tx_look_up_on_chain = terra.tx.tx_info(tx_hash)
        sleep(1)
        return tx_look_up_on_chain

    except LCDResponseError as err:
        raise Exception(err)


# Get the balances of all 3 assets and return it as an array
def get_balances(notify_balance=True):
    luna_balance = get_balance(account_address, "uluna")
    bluna_balance = get_balance(account_address, "bluna")
    ust_balance = get_balance(account_address, "uusd")

    if notify_balance:
        notify(
            f"Balance: Luna {luna_balance} | Bluna {bluna_balance} | UST {ust_balance}"
        )

    return [luna_balance, bluna_balance, ust_balance]


def setup_message():
    luna_to_bluna_ratio = float(os.getenv("LUNA_TO_BLUNA_RATIO"))
    bluna_to_luna_ratio = float(os.getenv("BLUNA_TO_LUNA_RATIO"))
    min_trade_balance = float(os.getenv("MIN_TRADE_BALANCE"))
    min_ust_balance = float(os.getenv("MIN_UST_BALANCE"))
    target_ust_balance = float(os.getenv("TARGET_UST_BALANCE"))
    sleep_duration = float(os.getenv("SLEEP_DURATION"))

    notify("ArBluna - v0.1\nMade by Luigi311\nFeel free to donate here")
    notify("terra18unmcxtftdkuqzqflzce9nmvyr07wfah43ps2m")

    notify(
        f"Config\nConverting luna to bluna above {luna_to_bluna_ratio}\nConverting bluna to luna above {bluna_to_luna_ratio}\nMinimum (b)luna to trade {min_trade_balance}\nMinimum UST Balance {min_ust_balance}\nTarget UST Balance {target_ust_balance}\nMax Spread: {spread}\nChecking every {sleep_duration} seconds\nWallet {account_address}"
    )
