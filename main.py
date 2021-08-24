# Set to python3
#!/usr/bin/env python3

import os, traceback
import distutils.util
from time import sleep
from dotenv import load_dotenv
from scripts.send_notification import notify
from scripts.telegram_bot import setup_bot
from scripts.get_info import get_ratio
from scripts.terra import execute_swap, check_tx_info, get_balances, setup_message

load_dotenv()

mnemonic = os.getenv("MNEMONIC")
luna_to_bluna_ratio = float(os.getenv("LUNA_TO_BLUNA_RATIO"))
bluna_to_luna_ratio = float(os.getenv("BLUNA_TO_LUNA_RATIO"))
min_trade_balance = float(os.getenv("MIN_TRADE_BALANCE"))
min_ust_balance = float(os.getenv("MIN_UST_BALANCE"))
target_ust_balance = float(os.getenv("TARGET_UST_BALANCE"))
sleep_duration = float(os.getenv("SLEEP_DURATION"))
notify_telegram = bool(distutils.util.strtobool(os.getenv("NOTIFY_TELEGRAM")))


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
        price = get_ratio("ust", luna_balance)
        # Calculate how much luna to sell to get to target UST balance
        amount = target_ust_balance / price

        # Check to see that we will have enough luna to sell and stay above the minimum set to trade
        if (luna_balance - amount) > min_trade_balance:
            notify("Selling some luna for UST")
            execute_swap(amount, "ust", price)
            luna_balance, bluna_balance, ust_balance = get_balances()

            if ust_balance < min_ust_balance:
                message = (
                    f"Error: UST balance of {ust_balance} should be higher\nExiting"
                )
                raise Exception(message)
        else:
            message = (
                "Not enough luna to sell while staying above the minimum trade balance"
            )
            raise Exception(message)
    else:
        luna_balance, bluna_balance, ust_balance = get_balances(notify_balance=False)

    return luna_balance, bluna_balance, ust_balance


def luna_bluna_trade(
    luna_balance: float,
    sleep_duration: float,
    min_trade_balance: float,
):
    # Get luna to BLuna price
    price = get_ratio("bluna", luna_balance)
    maximum = price

    # Flag to only notify once when the price is above the ratio to start swapping for bluna
    flag_buy = True
    while True:
        if flag_buy:
            notify("Price is less than threshold\nMonitoring for price increase")
            flag_buy = False

        # Continously check the price to see if the price is decreasing or increase
        price = get_ratio("bluna", luna_balance)

        # If the price is still increasing keep waiting
        if price > maximum:
            maximum = price

        # If the price starts to decrease and price is still above the target ratio swap for bluna
        if price < maximum and price > luna_to_bluna_ratio:
            notify("Executing trade")
            tx_hash = execute_swap(luna_balance, "bluna", price)
            tx_info = check_tx_info(tx_hash)

            luna_balance, bluna_balance, ust_balance = get_balances()

            # Check to see if the transaction was successful
            # if it failed the luna balance will be higher than the minimum trade balance so it should notify the user and exit
            if luna_balance > min_trade_balance:
                message = [
                    f"Error: Luna balance of {luna_balance} should be low",
                    f"{tx_info}",
                ]
                raise Exception(message)
            else:
                return luna_balance, bluna_balance, ust_balance
        else:
            # Delay to avoid spamming the API
            sleep(sleep_duration)


def bluna_luna_trade(
    bluna_balance: float,
    sleep_duration: float,
    min_trade_balance: float,
):
    # Get BLuna to LUNA price
    price = get_ratio("luna", bluna_balance)
    maximum = price

    # Flag to only notify once when the price is above the ratio to start swapping for luna
    flag_sell = True
    while True:
        if flag_sell:
            notify("Price is greater than threshold\nMonitoring for price decrease")
            flag_sell = False

        # Continously check the price to see if the price is increasing or decreasing
        price = get_ratio("luna", bluna_balance)

        # If the price is still increasing keep waiting
        if price > maximum:
            maximum = price

        # If the price starts to decrease swap for luna, and price is still above the target ratio
        if price < maximum and price > bluna_to_luna_ratio:
            notify("Executing trade")
            tx_hash = execute_swap(bluna_balance, "luna", price)
            tx_info = check_tx_info(tx_hash)

            luna_balance, bluna_balance, ust_balance = get_balances()

            # Check to see if the transaction was successful
            # if it failed the bluna balance will be higher than the minimum trade balance so it should notify the user and exit
            if bluna_balance > min_trade_balance:
                message = [
                    f"Error: BLuna balance of {bluna_balance} should be low\nExiting",
                    f"{tx_info}",
                ]
                raise Exception(message)
            else:
                return luna_balance, bluna_balance, ust_balance

        else:
            # Delay to avoid spamming the API
            sleep(sleep_duration)


def main() -> None:
    # Check to see if mnemonic is set
    if mnemonic == None or mnemonic == "":
        raise Exception(
            "Please set your mnemonic in the .env file or enviornment variable"
        )

    if notify_telegram:
        setup_bot()

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

            price = get_ratio("bluna", luna_balance)

            # When price is greater than the buying ratio start checking for price increase and then swap for bluna
            if price > luna_to_bluna_ratio:
                luna_balance, bluna_balance, ust_balance = luna_bluna_trade(
                    luna_balance, sleep_duration, min_trade_balance
                )

            # Check to see if we no longer have enough luna to sell to avoid having to sleep after a sucessful swap
            if luna_balance < min_trade_balance:
                break

            sleep(sleep_duration)

        # Flag to only notify once when monitoring to swap bluna for luna
        flag_start = True
        while bluna_balance > min_trade_balance:
            if flag_start:
                notify("Starting to monitor for BLuna -> Luna")
                flag_start = False

            price = get_ratio("luna", bluna_balance)

            # When price is greater than the selling ratio start checking for price decrease and then swap for luna
            if price > bluna_to_luna_ratio:
                luna_balance, bluna_balance, ust_balance = bluna_luna_trade(
                    bluna_balance, sleep_duration, min_trade_balance
                )

            # Check to see if we no longer have enough bluna to sell to avoid having to sleep after a sucessful swap
            if bluna_balance < min_trade_balance:
                break

            sleep(sleep_duration)


if __name__ == "__main__":
    try:
        main()

    except Exception as error:
        notify("ERROR!")

        if isinstance(error, list):
            for message in error:
                notify(message)
        else:
            notify(f"{error}")

        notify("Exiting")

        print(traceback.format_exc())

        os._exit(1)

    except KeyboardInterrupt:
        notify("Exiting")
        os._exit(1)
