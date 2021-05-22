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

# use for environment variables
import os

# use if needed to pass args to external modules
import sys

# used to create threads & dynamic loading of modules
import threading
import importlib

# used for directory handling
import glob

# Needed for colorful console output Install with: python3 -m pip install colorama (Mac/Linux) or pip install colorama (PC)
from colorama import init
init()

# needed for the binance API / websockets / Exception handling
from binance.client import Client
from binance.exceptions import BinanceAPIException

# used for dates
from datetime import date, datetime, timedelta
import time

# used to repeatedly execute the code
from itertools import count

# used to store trades and sell assets
import json

# Load helper modules
from helpers.parameters import (
    parse_args, load_config
)

# Load creds modules
from helpers.handle_creds import (
    load_correct_creds, test_api_key
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


if __name__ == '__main__':
    # Load arguments then parse settings
    args = parse_args()
    mymodule = {}
    DEFAULT_CONFIG_FILE = 'config.yml'
    DEFAULT_CREDS_FILE = 'creds.yml'

    config_file = args.config if args.config else DEFAULT_CONFIG_FILE
    creds_file = args.creds if args.creds else DEFAULT_CREDS_FILE
    parsed_config = load_config(config_file)
    parsed_creds = load_config(creds_file)

    # Default no debugging
    DEBUG = False

    # Load system vars
    TEST_MODE = parsed_config['script_options']['TEST_MODE']
    LOG_TRADES = parsed_config['script_options'].get('LOG_TRADES')
    LOG_FILE = parsed_config['script_options'].get('LOG_FILE')
    DEBUG_SETTING = parsed_config['script_options'].get('DEBUG')

    # Load trading vars
    PAIR_WITH = parsed_config['trading_options']['PAIR_WITH']
    QUANTITY = parsed_config['trading_options']['QUANTITY']
    MAX_COINS = parsed_config['trading_options']['MAX_COINS']
    FIATS = parsed_config['trading_options']['FIATS']
    TIME_DIFFERENCE = parsed_config['trading_options']['TIME_DIFFERENCE']
    RECHECK_INTERVAL = parsed_config['trading_options']['RECHECK_INTERVAL']
    CHANGE_IN_PRICE = parsed_config['trading_options']['CHANGE_IN_PRICE']
    STOP_LOSS = parsed_config['trading_options']['STOP_LOSS']
    TAKE_PROFIT = parsed_config['trading_options']['TAKE_PROFIT']
    CUSTOM_LIST = parsed_config['trading_options']['CUSTOM_LIST']
    USE_TRAILING_STOP_LOSS = parsed_config['trading_options']['USE_TRAILING_STOP_LOSS']
    TRAILING_STOP_LOSS = parsed_config['trading_options']['TRAILING_STOP_LOSS']
    TRAILING_TAKE_PROFIT = parsed_config['trading_options']['TRAILING_TAKE_PROFIT']
    SIGNALLING_MODULES = parsed_config['trading_options']['SIGNALLING_MODULES']
    if DEBUG_SETTING or args.debug:
        DEBUG = True

    # Load creds for correct environment
    access_key, secret_key = load_correct_creds(parsed_creds)

    if DEBUG:
        print(f'loaded config below\n{json.dumps(parsed_config, indent=4)}')
        print(f'Your credentials have been loaded from {creds_file}')


    # Authenticate with the client, Ensure API key is good before continuing
    client = Client(access_key, secret_key)
    api_ready, msg = test_api_key(client, BinanceAPIException)
    if api_ready is not True:
        exit(f'{txcolors.SELL_LOSS}{msg}{txcolors.DEFAULT}')

    # Use CUSTOM_LIST symbols if CUSTOM_LIST is set to True
    if CUSTOM_LIST: tickers=[line.strip() for line in open('tickers.txt')]

    # try to load all the coins bought by the bot if the file exists and is not empty
    coins_bought = {}

    # path to the saved coins_bought file
    coins_bought_file_path = 'coins_bought.json'

    # rolling window of prices; cyclical queue
    historical_prices = [None] * (TIME_DIFFERENCE * RECHECK_INTERVAL)
    hsp_head = -1

    # prevent including a coin in volatile_coins if it has already appeared there less than TIME_DIFFERENCE minutes ago
    volatility_cooloff = {}

    # use separate files for testing and live trading
    if TEST_MODE:
        coins_bought_file_path = 'test_' + coins_bought_file_path

    # if saved coins_bought json file exists and it's not empty then load it
    if os.path.isfile(coins_bought_file_path) and os.stat(coins_bought_file_path).st_size!= 0:
        with open(coins_bought_file_path) as file:
                coins_bought = json.load(file)

    print('Press Ctrl-Q to stop the script')

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
    binance_service.get_price()
    should_sell = False
    while True:
        if redis_service.binance_detect_mooning_job_status():
            orders, last_price, volume = binance_service.buy()
            binance_service.update_portfolio(orders, last_price, volume)
            coins_sold = binance_service.sell_coins()
            binance_service.remove_from_portfolio(coins_sold)
            should_sell = True
        elif should_sell:
            coins_sold = binance_service.panic_sell_coins()
            binance_service.remove_from_portfolio(coins_sold)
            should_sell = False
        else:
            print('Daemon is stopped, use de start endpoint if you want to become rich')
