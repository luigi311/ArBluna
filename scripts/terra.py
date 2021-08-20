import os
from terra_sdk.core.coins import Coins
from terra_sdk.core.coins import Coin
from terra_sdk.core.auth import StdFee
from terra_sdk.core.wasm import MsgExecuteContract
from terra_sdk.exceptions import LCDResponseError
from scripts.send_notification import notify, notify_swap
from time import sleep
from dotenv import load_dotenv
load_dotenv()



denominator = 1000000

def execute_swap(amount: float, to_token: str, price: float, wallet: any, terra: any):
    fee_estimation = int(0.15*denominator)
    amount = int(amount * denominator)    

    luna_bluna_pair_address = os.getenv('LUNA_BLUNA_PAIR_ADDRESS')
    bluna_contract = os.getenv('BLUNA_CONTRACT')
    luna_ust_pair_address = os.getenv('LUNA_UST_PAIR_ADDRESS')


    if to_token == 'bluna':
        coin = Coin('uluna', amount).to_data()
        coins = Coins.from_data([coin])
        send = MsgExecuteContract(
            sender=wallet.key.acc_address,
            contract=luna_bluna_pair_address,
            execute_msg={
                'swap': {
                    'offer_asset': {
                        'info' : {
                            'native_token': {
                                'denom': 'uluna'
                            }
                        },
                        'amount': str(int(amount))
                    },
                    'to': wallet.key.acc_address
                }
            },
            coins=coins
        ),
    elif to_token  == 'luna':
        send = MsgExecuteContract(
            sender=wallet.key.acc_address,
            contract=bluna_contract,
            execute_msg={
                'send': {
                    'contract': luna_bluna_pair_address,
                    'amount': str(int(amount)),
                    'msg': 'eyJzd2FwIjp7fX0='
                }
            },
            coins=Coins()
        ),
    elif to_token == 'uusd':
        coin = Coin('uluna', amount).to_data()
        coins = Coins.from_data([coin])
        send = MsgExecuteContract(
            sender=wallet.key.acc_address,
            contract=luna_ust_pair_address,
            execute_msg={
                'swap': {
                    'offer_asset': {
                        'info' : {
                            'native_token': {
                                'denom': 'uluna'
                            }
                        },
                        'amount': str(int(amount))
                    }
                }
            },
            coins=coins
        ),
    else:
        print('Invalid Token')
        exit(1)

    fee = str(int(fee_estimation)) + 'uusd'
    sendtx = wallet.create_and_sign_tx(send, fee=StdFee(denominator, fee))
    result = terra.tx.broadcast(sendtx)

    notify_swap(amount, 'luna', price)

    return result.txhash

def check_tx_info(tx_hash: str, terra: any):
    try:
        tx_look_up_on_chain = terra.tx.tx_info(tx_hash)
        sleep(1)
        return tx_look_up_on_chain

    except LCDResponseError as err:
        notify(err)
        exit(1)