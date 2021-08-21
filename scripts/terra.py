import os
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

load_dotenv()

chain_id = "columbus-4"
public_node_url = os.getenv("PUBLIC_NODE_URL")
mnemonic = os.getenv("MNEMONIC")
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
    # When swapping to luna, create structure for contract token to native token swap
    # Must point to luna_bluna_pair_address, it will automatically pull in the bLuna coin and send the luna to the sender address
    elif to_token == "luna":
        send = (
            MsgExecuteContract(
                sender=account_address,
                contract=bluna_contract,
                execute_msg={
                    "send": {
                        "contract": luna_bluna_pair_address,
                        "amount": str(int(amount)),
                        "msg": "eyJzd2FwIjp7fX0=",
                    }
                },
                coins=Coins(),
            ),
        )
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
                        "offer_asset": {
                            "info": {"native_token": {"denom": "uluna"}},
                            "amount": str(int(amount)),
                        }
                    }
                },
                coins=coins,
            ),
        )
    else:
        print("Invalid Token")
        exit(1)

    # Set fee to $0.15 UST, needs to be int to remove any decimals before casting to string
    fee = str(int(0.15 * denominator)) + "uusd"

    # Send transaction to execute contract
    sendtx = wallet.create_and_sign_tx(send, fee=StdFee(denominator, fee))
    result = terra.tx.broadcast(sendtx)

    # Notify the user about the transaction
    notify_swap(amount / denominator, "luna", price)

    return result.txhash


# Check the transaction status of the swap
# Source: https://github.com/unl1k3ly/AnchorHODL
def check_tx_info(tx_hash: str):
    try:
        tx_look_up_on_chain = terra.tx.tx_info(tx_hash)
        sleep(1)
        return tx_look_up_on_chain

    except LCDResponseError as err:
        notify(err)
        exit(1)


# Get the balances of all 3 assets and return it as an array
def get_balances():
    luna_balance = get_balance(account_address, "uluna")
    bluna_balance = get_balance(account_address, "bluna")
    ust_balance = get_balance(account_address, "uusd")

    notify(f"Balance: Luna {luna_balance} | Bluna {bluna_balance} | UST {ust_balance}")

    return [luna_balance, bluna_balance, ust_balance]


def setup_message():
    buy_ratio = float(os.getenv("BUY_RATIO"))
    sell_ratio = float(os.getenv("SELL_RATIO"))
    min_trade_balance = float(os.getenv("MIN_TRADE_BALANCE"))
    min_ust_balance = float(os.getenv("MIN_UST_BALANCE"))
    target_ust_balance = float(os.getenv("TARGET_UST_BALANCE"))
    sleep_duration = float(os.getenv("SLEEP_DURATION"))

    notify(f"ArBluna - v0.1\nMade by Luigi311\nFeel free to donate here")
    notify("terra18unmcxtftdkuqzqflzce9nmvyr07wfah43ps2m")

    notify(
        f"Config\nBuy below {buy_ratio}\nSell above {sell_ratio}\nMinimum (b)luna to trade {min_trade_balance}\nMinimum UST Balance {min_ust_balance}\nTarget UST Balance {target_ust_balance}\nChecking every {sleep_duration} seconds\nWallet {account_address}"
    )
