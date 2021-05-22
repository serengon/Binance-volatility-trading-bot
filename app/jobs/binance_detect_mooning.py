"""
Disclaimer
All investment strategies and investments involve risk of loss.
Nothing contained in this program, scripts, code or repositoy should be
construed as investment advice.Any reference to an investment's past or
potential performance is not, and should not be construed as, a recommendation
or as a guarantee of any specific outcome or profit.
By using this program you accept all liabilities,
and that no claims can be made against the developers,
or others connected with the program.
"""

# used to create threads & dynamic loading of modules
import threading
import importlib

# Needed for colorful console output Install with: python3 -m pip install colorama (Mac/Linux) or pip install colorama (PC)
from colorama import init
init()
import time

# used to repeatedly execute the code
from itertools import count

# used to store trades and sell assets
import json

# Load helper modules
from helpers.parameters import (
    parse_args, load_config
)

from app.services import binance as binance_service
from app.services import redis as redis_service

# for colourful logging to the console
class txcolors:
    BUY = '\033[92m'
    WARNING = '\033[93m'
    SELL_LOSS = '\033[91m'
    SELL_PROFIT = '\033[32m'
    DIM = '\033[2m\033[35m'
    DEFAULT = '\033[39m'


def run():
    # Load arguments then parse settings
    args = parse_args()
    mymodule = {}
    DEFAULT_CONFIG_FILE = 'config.yml'
    DEFAULT_CREDS_FILE = 'creds.yml'

    config_file = args.config if args.config else DEFAULT_CONFIG_FILE
    creds_file = args.creds if args.creds else DEFAULT_CREDS_FILE
    parsed_config = load_config(config_file)
    parsed_creds = load_config(creds_file)

    TEST_MODE = parsed_config['script_options']['TEST_MODE']
    SIGNALLING_MODULES = parsed_config['trading_options']['SIGNALLING_MODULES']

    print(f'loaded config below\n{json.dumps(parsed_config, indent=4)}')
    print(f'Your credentials have been loaded from {creds_file}')


    if not TEST_MODE:
        if not args.notimeout: # if notimeout skip this (fast for dev tests)
            print('WARNING: You are using the Mainnet and live funds. Waiting 30 seconds as a security measure')
            time.sleep(30)

    # load signalling modules
    for module in SIGNALLING_MODULES:
        mymodule[module] = importlib.import_module(module)
        t = threading.Thread(target=mymodule[module].do_work, args=())
        t.start()

    # seed initial prices
    binance_client = binance_service.BinanceClient(parsed_config, parsed_creds)
    binance_client.get_price()
    should_sell = False
    while True:
        if redis_service.binance_detect_mooning_job_status():
            orders, last_price, volume = binance_client.buy()
            binance_client.update_portfolio(orders, last_price, volume)
            coins_sold = binance_client.sell_coins()
            binance_client.remove_from_portfolio(coins_sold)
            should_sell = True
        elif should_sell:
            coins_sold = binance_client.panic_sell_coins()
            binance_client.remove_from_portfolio(coins_sold)
            should_sell = False
        else:
            print('Daemon is stopped, use the start endpoint if you want to become rich')


if __name__ == '__main__':
    run()
