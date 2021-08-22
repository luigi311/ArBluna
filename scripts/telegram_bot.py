import os
import distutils.util

from telegram import Update
from telegram.ext import Updater, CommandHandler, Filters, CallbackContext
from dotenv import load_dotenv

from scripts.get_info import get_ratio
from scripts.terra import get_balances, execute_swap

load_dotenv()
notify_telegram = bool(distutils.util.strtobool(os.getenv("NOTIFY_TELEGRAM")))

if notify_telegram:
    telegram_chat_id = int(os.getenv("TELEGRAM_CHAT_ID"))
    token = os.getenv("TELEGRAM_TOKEN")


def ping_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /ping is issued."""
    update.message.reply_text("pong")


def help_command(update: Update, context: CallbackContext) -> None:
    """Send list of commands when /help is issued."""
    update.message.reply_text(
        "Commands:\n/ping check if thebot is online\n/bluna get the bluna ratio\n/ust get the ust ratio\n/balance get the balances"
    )


def bluna_command(update: Update, context: CallbackContext) -> None:
    """Send the current luna to bluna ratio"""
    bluna = get_ratio("bluna")
    update.message.reply_text(f"Luna to Bluna ratio: {bluna}")


def ust_command(update: Update, context: CallbackContext) -> None:
    """Send the current luna to bluna ratio"""
    bluna = get_ratio("ust")
    update.message.reply_text(f"Luna to UST price: {bluna}")


def balance_command(update: Update, context: CallbackContext) -> None:
    """Send the current balances of the account"""
    get_balances()


def swap_to_bluna_command(update: Update, context: CallbackContext) -> None:
    """Force swap to bluna"""
    price = get_ratio("bluna")
    luna_balance, bluna_balance, ust_balance = get_balances()
    if luna_balance > 0 and ust_balance > 0.15:
        execute_swap(luna_balance, "bluna", price)
    else:
        raise Exception(f"Not enough luna {luna_balance} or ust {ust_balance}")


def swap_to_luna_command(update: Update, context: CallbackContext) -> None:
    """Force swap to luna"""
    price = get_ratio("bluna")
    luna_balance, bluna_balance, ust_balance = get_balances()
    if bluna_balance > 0 and ust_balance > 0.15:
        execute_swap(bluna_balance, "luna", price)
    else:
        raise Exception(f"Not enough bluna {bluna_balance} or ust {ust_balance}")


def setup_bot() -> None:
    try:
        """Start the bot."""
        # Create the Updater and pass it your bot's token.
        updater = Updater(token, use_context=True)

        # Get the dispatcher to register handlers
        dispatcher = updater.dispatcher

        # on different commands - answer in Telegram
        dispatcher.add_handler(
            CommandHandler(
                "help", help_command, filters=Filters.chat(chat_id=telegram_chat_id)
            )
        )
        dispatcher.add_handler(
            CommandHandler(
                "ping", ping_command, filters=Filters.chat(chat_id=telegram_chat_id)
            )
        )
        dispatcher.add_handler(
            CommandHandler(
                "bluna", bluna_command, filters=Filters.chat(chat_id=telegram_chat_id)
            )
        )
        dispatcher.add_handler(
            CommandHandler(
                "ust", ust_command, filters=Filters.chat(chat_id=telegram_chat_id)
            )
        )
        dispatcher.add_handler(
            CommandHandler(
                "balance",
                balance_command,
                filters=Filters.chat(chat_id=telegram_chat_id),
            )
        )
        dispatcher.add_handler(
            CommandHandler(
                "balances",
                balance_command,
                filters=Filters.chat(chat_id=telegram_chat_id),
            )
        )
        dispatcher.add_handler(
            CommandHandler(
                "swap_to_bluna",
                swap_to_bluna_command,
                filters=Filters.chat(chat_id=telegram_chat_id),
            )
        )
        dispatcher.add_handler(
            CommandHandler(
                "swap_to_luna",
                swap_to_luna_command,
                filters=Filters.chat(chat_id=telegram_chat_id),
            )
        )

        # Start the Bot
        updater.start_polling()

    except Exception as e:
        raise Exception(f"Telegram bot error: {e}")