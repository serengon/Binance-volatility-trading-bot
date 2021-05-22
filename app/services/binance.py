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


# for colourful logging to the console
class txcolors:
    BUY = '\033[92m'
    WARNING = '\033[93m'
    SELL_LOSS = '\033[91m'
    SELL_PROFIT = '\033[32m'
    DIM = '\033[2m\033[35m'
    DEFAULT = '\033[39m'

# tracks profit/loss each session
#global session_profit
#session_profit = 0

client = None

class BinanceClient:

    def __init__(self, parsed_config, parsed_creds):
        # Load creds for correct environment
        access_key, secret_key = load_correct_creds(parsed_creds)
        self.client = Client(access_key, secret_key)
        api_ready, msg = test_api_key(client, BinanceAPIException)
        if api_ready is not True:
            raise Exception(msg)

        # Load system vars
        self.test_mode = parsed_config['script_options']['TEST_MODE']
        self.log_trades = parsed_config['script_options'].get('LOG_TRADES')
        self.log_file = parsed_config['script_options'].get('LOG_FILE')
        self.debug = parsed_config['script_options'].get('DEBUG') or False

        # Load trading vars
        self.custom_list = parsed_config['trading_options']['CUSTOM_LIST']
        self.pair_with = parsed_config['trading_options']['PAIR_WITH']
        self.fiats = parsed_config['trading_options']['FIATS']
        self.time_difference = parsed_config['trading_options']['TIME_DIFFERENCE']
        self.recheck_interval = parsed_config['trading_options']['RECHECK_INTERVAL']
        self.change_in_price = parsed_config['trading_options']['CHANGE_IN_PRICE']
        self.max_coins = parsed_config['trading_options']['MAX_COINS']
        self.quantity = parsed_config['trading_options']['QUANTITY']
        self.stop_loss = parsed_config['trading_options']['STOP_LOSS']
        self.take_profit = parsed_config['trading_options']['TAKE_PROFIT']
        self.user_trailing_stop_loss = parsed_config['trading_options']['USE_TRAILING_STOP_LOSS']
        self.trailing_stop_loss = parsed_config['trading_options']['TRAILING_STOP_LOSS']
        self.trailing_take_profit = parsed_config['trading_options']['TRAILING_TAKE_PROFIT']

        # rolling window of prices; cyclical queue
        self.historical_prices = [None] * (self.time_difference * self.recheck_interval)
        self.hsp_head = -1

        self.coins_bought = {}
        # path to the saved coins_bought file
        self.coins_bought_file_path = 'coins_bought.json'

        # use separate files for testing and live trading
        if self.test_mode:
            self.coins_bought_file_path = 'test_' + self.coins_bought_file_path

        # if saved coins_bought json file exists and it's not empty then load it
        if os.path.isfile(self.coins_bought_file_path) and os.stat(self.coins_bought_file_path).st_size != 0:
            with open(self.coins_bought_file_path) as file:
                self.coins_bought = json.load(file)

        # prevent including a coin in volatile_coins if it has already appeared there less than TIME_DIFFERENCE minutes ago
        self.volatility_cooloff = {}

        # Use CUSTOM_LIST symbols if CUSTOM_LIST is set to True
        self.tickers = [line.strip() for line in open('tickers.txt')] if self.custom_list else []

        # tracks profit/loss each session
        self.session_profit = 0

    def get_price(self, add_to_historical=True):
        '''Return the current price for all coins on binance'''

        initial_price = {}
        prices = self.client.get_all_tickers()

        for coin in prices:

            if self.custom_list:
                if (
                        any(item + self.pair_with == coin['symbol'] for item in self.tickers)
                        and all(item not in coin['symbol'] for item in self.fiats)
                ):
                    initial_price[coin['symbol']] = {'price': coin['price'], 'time': datetime.now()}
            else:
                if self.pair_with in coin['symbol'] and all(item not in coin['symbol'] for item in self.fiats):
                    initial_price[coin['symbol']] = {'price': coin['price'], 'time': datetime.now()}

        if add_to_historical:
            self.hsp_head = (self.hsp_head + 1) % (self.time_difference * self.recheck_interval)
            self.historical_prices[self.hsp_head] = initial_price

        return initial_price


    def _wait_for_price(self):
        '''calls the initial price and ensures the correct amount of time has passed
        before reading the current price again'''

        volatile_coins = {}
        externals = {}

        coins_up = 0
        coins_down = 0
        coins_unchanged = 0

        if self.historical_prices[self.hsp_head]['BNB' + self.pair_with]['time'] > datetime.now() - timedelta(
                minutes=float(self.time_difference / self.recheck_interval)):
            # sleep for exactly the amount of time required
            time.sleep(
                (
                        timedelta(minutes=float(self.time_difference / self.recheck_interval))
                        - (datetime.now() - self.historical_prices[self.hsp_head]['BNB' + self.pair_with]['time'])
                ).total_seconds()
            )

        print(f'not enough time has passed yet...Session profit:{self.session_profit:.2f}%')

        # retreive latest prices
        self.get_price()

        # calculate the difference in prices
        for coin in self.historical_prices[self.hsp_head]:
            # minimum and maximum prices over time period
            min_price = min(
                self.historical_prices,
                key=lambda x: float("inf") if x is None else float(x[coin]['price'])
            )
            max_price = max(self.historical_prices, key=lambda x: -1 if x is None else float(x[coin]['price']))

            threshold_check = (-1.0 if min_price[coin]['time'] > max_price[coin]['time'] else 1.0)\
                              * (float(max_price[coin]['price']) - float(min_price[coin]['price']))\
                              / float(min_price[coin]['price']) * 100

            # each coin with higher gains than our CHANGE_IN_PRICE is added to the volatile_coins dict if less than MAX_COINS is not reached.
            if threshold_check > self.change_in_price:
                coins_up += 1

                if coin not in self.volatility_cooloff:
                    self.volatility_cooloff[coin] = datetime.now() - timedelta(minutes=self.time_difference)

                # only include coin as volatile if it hasn't been picked up in the last TIME_DIFFERENCE minutes already
                if datetime.now() >= self.volatility_cooloff[coin] + timedelta(minutes=self.time_difference):
                    self.volatility_cooloff[coin] = datetime.now()

                    if len(self.coins_bought) + len(volatile_coins) < self.max_coins or self.max_coins == 0:
                        volatile_coins[coin] = round(threshold_check, 3)
                        print(f'{coin} has gained {volatile_coins[coin]}% within the last {self.time_difference} min, '
                              f'calculating volume in {self.pair_with}')

                    else:
                        print(
                            f'{txcolors.WARNING}{coin} has gained {round(threshold_check, 3)}% within the last '
                            f'{self.time_difference} min, but you are holding max number of coins{txcolors.DEFAULT}')

            elif threshold_check < self.change_in_price:
                coins_down += 1

            else:
                coins_unchanged += 1
        # Disabled until fix
        # print(f'Up: {coins_up} Down: {coins_down} Unchanged: {coins_unchanged}')

        # Here goes new code for external signalling
        externals = self._external_signals()
        exnumber = 0
        for excoin in externals:
            if (
                    excoin not in volatile_coins
                    and excoin not in self.coins_bought
                    and (len(self.coins_bought) + exnumber) < self.max_coins
            ):
                volatile_coins[excoin] = 1
                exnumber += 1
                print(f'External signal received on {excoin}, calculating volume in {self.pair_with}')

        return volatile_coins, len(volatile_coins), self.historical_prices[self.hsp_head]

    def _external_signals(self):
        external_list = {}
        signals = {}

        # check directory and load pairs from files into external_list
        signals = glob.glob("signals/*.exs")
        for filename in signals:
            for line in open(filename):
                symbol = line.strip()
                external_list[symbol] = symbol
            os.remove(filename)

        return external_list

    def _convert_volume(self):
        '''Converts the volume given in QUANTITY from USDT to the each coin's volume'''

        volatile_coins, number_of_coins, last_price = self._wait_for_price()
        lot_size = {}
        volume = {}

        for coin in volatile_coins:

            # Find the correct step size for each coin
            # max accuracy for BTC for example is 6 decimal points
            # while XRP is only 1
            try:
                info = self.client.get_symbol_info(coin)
                step_size = info['filters'][2]['stepSize']
                lot_size[coin] = step_size.index('1') - 1

                if lot_size[coin] < 0:
                    lot_size[coin] = 0

            except:
                pass

            # calculate the volume in coin from QUANTITY in USDT (default)
            volume[coin] = float(self.quantity / float(last_price[coin]['price']))

            # define the volume with the correct step size
            if coin not in lot_size:
                volume[coin] = float('{:.1f}'.format(volume[coin]))

            else:
                # if lot size has 0 decimal points, make the volume an integer
                if lot_size[coin] == 0:
                    volume[coin] = int(volume[coin])
                else:
                    volume[coin] = float('{:.{}f}'.format(volume[coin], lot_size[coin]))

        return volume, last_price

    def buy(self):
        '''Place Buy market orders for each volatile coin found'''

        volume, last_price = self._convert_volume()
        orders = {}

        for coin in volume:

            # only buy if the there are no active trades on the coin
            if coin not in self.coins_bought:
                print(f"{txcolors.BUY}Preparing to buy {volume[coin]} {coin}{txcolors.DEFAULT}")

                if self.test_mode:
                    orders[coin] = [{
                        'symbol': coin,
                        'orderId': 0,
                        'time': datetime.now().timestamp()
                    }]

                    # Log trade
                    if self.log_trades:
                        self._write_log(f"Buy : {volume[coin]} {coin} - {last_price[coin]['price']}")

                    continue

                # try to create a real order if the test orders did not raise an exception
                try:
                    self.client.create_order(
                        symbol=coin,
                        side='BUY',
                        type='MARKET',
                        quantity=volume[coin]
                    )

                # error handling here in case position cannot be placed
                except Exception as e:
                    print(e)

                # run the else block if the position has been placed and return order info
                else:
                    orders[coin] = self.client.get_all_orders(symbol=coin, limit=1)

                    # binance sometimes returns an empty list, the code will wait here until binance returns the order
                    while not orders[coin]:
                        print('Binance is being slow in returning the order, calling the API again...')

                        orders[coin] = self.client.get_all_orders(symbol=coin, limit=1)
                        time.sleep(1)

                    else:
                        print('Order returned, saving order to file')

                        # Log trade
                        if self.log_trades:
                            self._write_log(f"Buy : {volume[coin]} {coin} - {last_price[coin]['price']}")


            else:
                print(f'Signal detected, but there is already an active trade on {coin}')

        return orders, last_price, volume

    def sell_coins(self):
        '''sell coins that have reached the STOP LOSS or TAKE PROFIT threshold'''

        last_price = self.get_price(False)  # don't populate rolling window
        coins_sold = {}

        for coin in self.coins_bought.keys():
            # define stop loss and take profit
            TP = float(self.coins_bought[coin]['bought_at']) + (
                        float(self.coins_bought[coin]['bought_at']) * self.coins_bought[coin]['take_profit']) / 100
            SL = float(self.coins_bought[coin]['bought_at']) + (
                        float(self.coins_bought[coin]['bought_at']) * self.coins_bought[coin]['stop_loss']) / 100

            LastPrice = float(last_price[coin]['price'])
            BuyPrice = float(self.coins_bought[coin]['bought_at'])
            PriceChange = float((LastPrice - BuyPrice) / BuyPrice * 100)

            # check that the price is above the take profit and readjust SL and TP accordingly if trialing stop loss used
            if float(last_price[coin]['price']) > TP and self.user_trailing_stop_loss:
                if self.debug:
                    print("TP reached, adjusting TP and SL accordingly to lock-in profit")

                # increasing TP by TRAILING_TAKE_PROFIT (essentially next time to readjust SL)
                self.coins_bought[coin]['take_profit'] = PriceChange + self.trailing_take_profit
                self.coins_bought[coin]['stop_loss'] = self.coins_bought[coin]['take_profit'] - self.trailing_stop_loss

                continue

            # check that the price is below the stop loss or above take profit (if trailing stop loss not used) and sell if this is the case
            if (
                    float(last_price[coin]['price']) < SL
                    or (float(last_price[coin]['price']) > TP and not self.user_trailing_stop_loss)
            ):
                print(f"{txcolors.SELL_PROFIT if PriceChange >= 0. else txcolors.SELL_LOSS}TP or SL reached, "
                      f"selling {self.coins_bought[coin]['volume']} {coin} - {BuyPrice} - {LastPrice} : "
                      f"{PriceChange:.2f}%{txcolors.DEFAULT}")

                # try to create a real order
                try:

                    if not self.test_mode:
                        sell_coins_limit = self.client.create_order(
                            symbol=coin,
                            side='SELL',
                            type='MARKET',
                            quantity=self.coins_bought[coin]['volume']

                        )

                # error handling here in case position cannot be placed
                except Exception as e:
                    print(e)

                # run the else block if coin has been sold and create a dict for each coin sold
                else:
                    coins_sold[coin] = self.coins_bought[coin]
                    # Log trade

                    if self.log_trades:
                        profit = (LastPrice - BuyPrice) * coins_sold[coin]['volume']
                        self._write_log(f"Sell: {coins_sold[coin]['volume']} {coin} - {BuyPrice} - {LastPrice} "
                                  f"Profit: {profit:.2f} {PriceChange:.2f}%")
                        self.session_profit = self.session_profit + PriceChange
                continue

            # no action; print once every TIME_DIFFERENCE
            if self.hsp_head == 1:
                print(f'TP or SL not yet reached, not selling {coin} for now {BuyPrice} - {LastPrice} '
                      f': {txcolors.SELL_PROFIT if PriceChange >= 0. else txcolors.SELL_LOSS}{PriceChange:.2f}'
                      f'%{txcolors.DEFAULT}')

        return coins_sold

    def panic_sell_coins(self):
        ''' sell all coins'''

        last_price = self.get_price(False)  # don't populate rolling window
        coins_sold = {}

        for coin in list(self.coins_bought):

            LastPrice = float(last_price[coin]['price'])
            BuyPrice = float(self.coins_bought[coin]['bought_at'])
            PriceChange = float((LastPrice - BuyPrice) / BuyPrice * 100)

            print(f"{txcolors.SELL_PROFIT if PriceChange >= 0. else txcolors.SELL_LOSS}Panic sell, stopping "
                  f"everything, selling {self.coins_bought[coin]['volume']} {coin} - {BuyPrice} - {LastPrice} : "
                  f"{PriceChange:.2f}%{txcolors.DEFAULT}")

            # try to create a real order
            try:

                if not self.test_mode:
                    self.client.create_order(
                        symbol=coin,
                        side='SELL',
                        type='MARKET',
                        quantity=self.coins_bought[coin]['volume']

                    )

            # error handling here in case position cannot be placed
            except Exception as e:
                print(e)

            # run the else block if coin has been sold and create a dict for each coin sold
            else:
                coins_sold[coin] = self.coins_bought[coin]
                # Log trade

                if self.log_trades:
                    profit = (LastPrice - BuyPrice) * coins_sold[coin]['volume']
                    self._write_log(f"Sell: {coins_sold[coin]['volume']} {coin} - {BuyPrice} - {LastPrice} Profit: "
                              f"{profit:.2f} {PriceChange:.2f}%")
                    self.session_profit = self.session_profit + PriceChange

        return coins_sold

    def update_portfolio(self, orders, last_price, volume):
        '''add every coin bought to our portfolio for tracking/selling later'''
        if self.debug:
            print(orders)
        for coin in orders:
            self.coins_bought[coin] = {
                'symbol': orders[coin][0]['symbol'],
                'orderid': orders[coin][0]['orderId'],
                'timestamp': orders[coin][0]['time'],
                'bought_at': last_price[coin]['price'],
                'volume': volume[coin],
                'stop_loss': -self.stop_loss,
                'take_profit': self.take_profit,
            }

            # save the coins in a json file in the same directory
            with open(self.coins_bought_file_path, 'w') as file:
                json.dump(self.coins_bought, file, indent=4)

            print(f'Order with id {orders[coin][0]["orderId"]} placed and saved to file')

    def remove_from_portfolio(self, coins_sold):
        '''Remove coins sold due to SL or TP from portfolio'''
        for coin in coins_sold:
            self.coins_bought.pop(coin)

        with open(self.coins_bought_file_path, 'w') as file:
            json.dump(self.coins_bought, file, indent=4)

    def _write_log(self, logline):
        timestamp = datetime.now().strftime("%d/%m %H:%M:%S")
        with open(self.log_file, 'a+') as f:
            f.write(timestamp + ' ' + logline + '\n')
