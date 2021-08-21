# ArBluna
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/00463263f34c433e9ab5e7c8e205bdba)](https://www.codacy.com/gh/luigi311/ArBluna/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=luigi311/ArBluna&amp;utm_campaign=Badge_Grade)  

Automatic arbritage for Bluna on terraswap

## Usage

### Recommended Docker

#### With variables

- Run

  ```bash
  docker run -e MNEMONIC='Seed Phrase Here' luigi311/arbluna:latest
  ```

#### With .env

- Create a .env file similar to .env.sample and set the MNEMONIC variable to your seed phrase
- Run

  ```bash
   docker run -v "$(pwd)/.env:/app/.env" luigi311/arbluna:latest
   ```

### Baremetal

- Setup virtualenv of your choice

- Install dependencies

  ```bash
    pip install -r requirements.txt
  ```

- Create a .env file similar to .env.sample and set the MNEMONIC variable to your seed phrase
- Run

  ```bash
  python main.py
  ```

## Shoutout to <https://github.com/unl1k3ly/AnchorHODL> that was used as a base for this project
