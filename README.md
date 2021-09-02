# ArBluna

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/00463263f34c433e9ab5e7c8e205bdba)](https://www.codacy.com/gh/luigi311/ArBluna/dashboard?utm_source=github.com&utm_medium=referral&utm_content=luigi311/ArBluna&utm_campaign=Badge_Grade)  

Automatic arbritage for Bluna on terraswap

## Usage

### Recommended Docker

#### With variables

-   Run

    ```bash
    docker run -e MNEMONIC='Seed Phrase Here' luigi311/arbluna:latest
    ```

#### With .env

-   Create a .env file similar to .env.sample and set the MNEMONIC variable to your seed phrase

-   Run

    ```bash
     docker run -v "$(pwd)/.env:/app/.env" luigi311/arbluna:latest
    ```

### Baremetal

-   Setup virtualenv of your choice

-   Install dependencies

    ```bash
      pip install -r requirements.txt
    ```

-   Create a .env file similar to .env.sample and set the MNEMONIC variable to your seed phrase

-   Run

    ```bash
    python main.py
    ```

### Telegram Bot

When using the notify_telegram option, you can use the following commands with the telegram bot:

-   /help - Show this help message
-   /ping - Check if the bot is running
-   /luna - Get the bluna -> luna ratio
-   /bluna - Get the luna -> bluna ratio
-   /ust - Check the current Luna to UST ratio
-   /balance - Check the current balances
-   /swap_to_bluna - To force a swap from luna to bluna
-   /swap_to_luna - To force a swap from bluna to luna

## Shoutout to <https://github.com/unl1k3ly/AnchorHODL> that was used as a base for this project
