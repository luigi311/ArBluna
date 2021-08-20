# Set to python3

import os
from terra_sdk.client.lcd import LCDClient
from terra_sdk.key.mnemonic import MnemonicKey
from time import sleep
from dotenv import load_dotenv
from scripts.send_notification import notify
from scripts.get_info import get_ratio, get_balances
from scripts.terra import execute_swap, check_tx_info


def main():
    load_dotenv()

    chain_id = "columbus-4"
    public_node_url = os.getenv("PUBLIC_NODE_URL")
    mnemonic = os.getenv("MNEMONIC")

    if mnemonic == None or mnemonic == "":
        notify("Please set your mnemonic in the .env file or enviornment variable")
        exit(1)

    # Connect to Testnet
    terra = LCDClient(chain_id=chain_id, url=public_node_url)
    # Desire wallet via passphrase
    mk = MnemonicKey(mnemonic=mnemonic)
    # Define what wallet to use
    wallet = terra.wallet(mk)
    # Account Add
    account_address = wallet.key.acc_address

    notify(f"ArBluna - v0.1\nMade by Luigi311\nFeel free to donate here")
    notify("terra18unmcxtftdkuqzqflzce9nmvyr07wfah43ps2m")

    buy_ratio = float(os.getenv("BUY_RATIO"))
    sell_ratio = float(os.getenv("SELL_RATIO"))
    min_trade_balance = float(os.getenv("MIN_TRADE_BALANCE"))
    min_ust_balance = float(os.getenv("MIN_UST_BALANCE"))
    target_ust_balance = float(os.getenv("TARGET_UST_BALANCE"))
    sleep_duration = float(os.getenv("SLEEP_DURATION"))

    notify(
        f"Config\nBuy below {buy_ratio}\nSell above {sell_ratio}\nMinimum (b)luna to trade {min_trade_balance}\nMinimum UST Balance {min_ust_balance}\nTarget UST Balance {target_ust_balance}\nChecking every {sleep_duration} seconds\nWallet {account_address}"
    )
    # Check balance
    luna_balance, bluna_balance, ust_balance = get_balances(account_address)

    while True:
        if ust_balance < min_ust_balance:
            notify("UST balance is less than the minimum set")
            price = get_ratio("ust")
            amount = target_ust_balance / price
            if (luna_balance - amount) > min_trade_balance:
                notify("Selling some luna for UST")
                execute_swap(amount, "ust", price, wallet)
                luna_balance, bluna_balance, ust_balance = get_balances(account_address)
            else:
                notify(
                    "Not enough luna to sell while staying above the minimum trade balance"
                )
                exit(1)

        flag_start = True
        while luna_balance > min_trade_balance:
            if flag_start:
                notify("Starting to monitor for Luna -> BLuna")
                flag_start = False
            price = get_ratio("bluna")
            min = price

            flag_buy = True
            while min < buy_ratio:
                if flag_buy:
                    notify(
                        f"Price is less than threshold\nMonitoring for price increase"
                    )
                    flag_buy = False
                price = get_ratio("bluna")

                if price < min:
                    min = price

                if price > min:
                    notify(f"Final: {price}\nExecuting trade")
                    tx_hash = execute_swap(luna_balance, "bluna", price, wallet)
                    tx_info = check_tx_info(tx_hash, terra)

                    luna_balance, bluna_balance, ust_balance = get_balances(
                        account_address
                    )

                    if luna_balance > min_trade_balance:
                        notify(
                            f"Error: Luna balance of {luna_balance} should be low\nExiting"
                        )
                        exit(1)
                    min = 1
                    break
                else:
                    sleep(sleep_duration / 2)
            if luna_balance < min_trade_balance:
                break
            sleep(sleep_duration)

        flag_start = True
        while bluna_balance > min_trade_balance:
            if flag_start:
                notify("Starting to monitor for BLuna -> Luna")
                flag_start = False

            price = get_ratio("bluna")
            max = price
            flag_sell = True
            while max > sell_ratio:
                if flag_sell:
                    notify(
                        f"Price is greater than threshold\nMonitoring for price decrease"
                    )
                    flag_sell = False
                price = get_ratio("bluna")

                if price > max:
                    max = price

                if price < max:
                    notify(f"Final: {price}\nExecuting trade")
                    tx_hash = execute_swap(bluna_balance, "luna", price, wallet)
                    tx_info = check_tx_info(tx_hash, terra)

                    luna_balance, bluna_balance, ust_balance = get_balances(
                        account_address
                    )
                    if bluna_balance > min_trade_balance:
                        notify(
                            f"Error: BLuna balance of {bluna_balance} should be low\nExiting"
                        )
                        exit(1)

                    max = 0
                    break
                else:
                    sleep(sleep_duration / 2)

            if bluna_balance < min_trade_balance:
                break
            sleep(sleep_duration)


if __name__ == "__main__":
    main()
