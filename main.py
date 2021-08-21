# Set to python3
#!/usr/bin/env python3

import os
from time import sleep
from dotenv import load_dotenv
from scripts.send_notification import notify
from scripts.get_info import get_ratio
from scripts.terra import execute_swap, check_tx_info, get_balances, setup_message


def min_ust_check(
    ust_balance: float,
    luna_balance: float,
    min_ust_balance: float,
    target_ust_balance: float,
    min_trade_balance: float,
):
    # Check to see if we are below the minimum UST balance, if so sell luna to reach target UST balance
    if ust_balance < min_ust_balance:
        notify("UST balance is less than the minimum set")
        # Get luna to UST price
        price = get_ratio("ust")
        # Calculate how much luna to sell to get to target UST balance
        amount = target_ust_balance / price

        # Check to see that we will have enough luna to sell and stay above the minimum set to trade
        if (luna_balance - amount) > min_trade_balance:
            notify("Selling some luna for UST")
            execute_swap(amount, "ust", price)
            luna_balance, bluna_balance, ust_balance = get_balances()

            if ust_balance < min_ust_balance:
                notify(f"Error: UST balance of {ust_balance} should be higher\nExiting")
                exit(1)
        else:
            notify(
                "Not enough luna to sell while staying above the minimum trade balance"
            )
            exit(1)
    else:
        luna_balance, bluna_balance, ust_balance = get_balances()

    return luna_balance, bluna_balance, ust_balance


def luna_bluna_trade(
    luna_balance: float,
    buy_ratio: float,
    sleep_duration: float,
    min_trade_balance: float,
):
    # Get luna to BLuna price
    price = get_ratio("bluna")
    minimum = price

    # Flag to only notify once when the price is below the ratio to start swapping for bluna
    flag_buy = True
    while minimum < buy_ratio:
        if flag_buy:
            notify("Price is less than threshold\nMonitoring for price increase")
            flag_buy = False

        # Continously check the price to see if the price is decreasing or increase
        price = get_ratio("bluna")

        # If the price is still decreasing keep waiting
        if price < minimum:
            minimum = price

        # If the price starts to increase swap for bluna
        if price > minimum:
            notify(f"Final: {price}\nExecuting trade")
            tx_hash = execute_swap(luna_balance, "bluna", price)
            tx_info = check_tx_info(tx_hash)

            luna_balance, bluna_balance, ust_balance = get_balances()

            # Check to see if the transaction was successful
            # if it failed the luna balance will be higher than the minimum trade balance so it should notify the user and exit
            if luna_balance > min_trade_balance:
                notify(f"Error: Luna balance of {luna_balance} should be low\nExiting")
                notify(f"tx_info: {tx_info}")
                exit(1)

            return luna_balance, bluna_balance, ust_balance
        else:
            # Check twice as often to see if the price is increasing or decreasing
            sleep(sleep_duration / 2)


def bluna_luna_trade(
    bluna_balance: float,
    sell_ratio: float,
    sleep_duration: float,
    min_trade_balance: float,
):
    # Get BLuna to LUNA price
    price = get_ratio("bluna")
    maximum = price

    # Flag to only notify once when the price is above the ratio to start swapping for luna
    flag_sell = True
    while maximum > sell_ratio:
        if flag_sell:
            notify("Price is greater than threshold\nMonitoring for price decrease")
            flag_sell = False

        # Continously check the price to see if the price is increasing or decreasing
        price = get_ratio("bluna")

        # If the price is still increasing keep waiting
        if price > maximum:
            maximum = price

        # If the price starts to decrease swap for luna
        if price < maximum:
            notify(f"Final: {price}\nExecuting trade")
            tx_hash = execute_swap(bluna_balance, "luna", price)
            tx_info = check_tx_info(tx_hash)

            luna_balance, bluna_balance, ust_balance = get_balances()

            # Check to see if the transaction was successful
            # if it failed the bluna balance will be higher than the minimum trade balance so it should notify the user and exit
            if bluna_balance > min_trade_balance:
                notify(
                    f"Error: BLuna balance of {bluna_balance} should be low\nExiting"
                )
                notify(f"tx_info: {tx_info}")

                exit(1)

            return luna_balance, bluna_balance, ust_balance
        else:
            # Check twice as often to see if the price is increasing or decreasing
            sleep(sleep_duration / 2)


def main():
    load_dotenv()

    # Check to see if mnemonic is set
    mnemonic = os.getenv("MNEMONIC")
    if mnemonic == None or mnemonic == "":
        notify("Please set your mnemonic in the .env file or enviornment variable")
        exit(1)

    buy_ratio = float(os.getenv("BUY_RATIO"))
    sell_ratio = float(os.getenv("SELL_RATIO"))
    min_trade_balance = float(os.getenv("MIN_TRADE_BALANCE"))
    min_ust_balance = float(os.getenv("MIN_UST_BALANCE"))
    target_ust_balance = float(os.getenv("TARGET_UST_BALANCE"))
    sleep_duration = float(os.getenv("SLEEP_DURATION"))

    setup_message()

    # Get the balances
    luna_balance, bluna_balance, ust_balance = get_balances()

    while True:
        luna_balance, bluna_balance, ust_balance = min_ust_check(
            ust_balance,
            luna_balance,
            min_ust_balance,
            target_ust_balance,
            min_trade_balance,
        )

        # Flag to only notify once when monitoring to swap luna for bluna
        flag_start = True
        while luna_balance > min_trade_balance:
            if flag_start:
                notify("Starting to monitor for Luna -> BLuna")
                flag_start = False

            luna_balance, bluna_balance, ust_balance = luna_bluna_trade(
                luna_balance, buy_ratio, sleep_duration, min_trade_balance
            )

            # Check to see if we no longer have enough luna to sell to avoid having to sleep after a sucessful swap
            if luna_balance < min_trade_balance:
                break

        # Flag to only notify once when monitoring to swap bluna for luna
        flag_start = True
        while bluna_balance > min_trade_balance:
            if flag_start:
                notify("Starting to monitor for BLuna -> Luna")
                flag_start = False

            luna_balance, bluna_balance, ust_balance = bluna_luna_trade(
                bluna_balance, sell_ratio, sleep_duration, min_trade_balance
            )

            # Check to see if we no longer have enough bluna to sell to avoid having to sleep after a sucessful swap
            if bluna_balance < min_trade_balance:
                break
            sleep(sleep_duration)


if __name__ == "__main__":
    main()
