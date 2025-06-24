import time
import threading
from datetime import datetime, timedelta
from executor import get_executor
from strategies import get_strategy
from utils.stop_loss import StopLossDetector
import config

TICKER = "KRW-BTC"
STRATEGY_NAME = "rsi"
EXECUTOR_TYPE = "mock"
INTERVAL = config.INTERVAL

INTERVAL_MAP = {
    "minute1": 60,
    "minute3": 180,
    "minute5": 300,
    "minute15": 900,
    "minute30": 1800,
    "minute60": 3600,
    "minute240": 14400,
    "day": 86400,
}
INTERVAL_SECONDS = INTERVAL_MAP[INTERVAL]
StopLossDetector.candle_interval_minutes = INTERVAL_SECONDS // 60

executor = get_executor(EXECUTOR_TYPE)
strategy = get_strategy(STRATEGY_NAME)

stop_signal = False
last_candle_time = None

def print_help():
    print("Available commands:")
    print(" - status | s      : Show account status")
    print(" - exit   | q      : Quit auto trading")
    print(" - help   | h | ?  : Show this help message")
    print(" - current| c      : Show current price")
    print(" - time   | t      : Show current time(Local)")

def input_listener():
    global stop_signal
    while True:
        cmd = input().strip().lower()
        if cmd == "":
            continue
        if cmd in ["exit", "q", "quit"]:
            stop_signal = True
            break
        elif cmd in ["status", "s"]:
            krw = executor.get_krw()
            btc = executor.get_btc()
            avg_price = executor.get_avg_buy_price(TICKER)
            print("Current Account Status:")
            print(f" - KRW Balance      : {krw:,.0f} KRW")
            print(f" - BTC Holdings     : {btc:.8f} BTC")
            if btc > 0 and avg_price > 0:
                print(f" - Avg Buy Price    : {avg_price:,.0f} KRW")
        elif cmd in ["current", "c"]:
            c_price = executor.get_current_price(TICKER)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Current Price: {c_price:,.0f} KRW")
        elif cmd in ["time", "t"]:
            print(f"[{datetime.now().strftime('%H:%M:%S')}]")
        elif cmd in ["help", "h", "?"]:
            print_help()
        else:
            print(f"[Unknown command] '{cmd}' — type 'help' to see available commands.")


threading.Thread(target=input_listener, daemon=True).start()

def wait_until_next_interval(interval_sec: int):
    global last_candle_time

    while not stop_signal:
        df = executor.fetch_ohlcv(TICKER, interval=INTERVAL).tail(1000)
        candle_time = df.index[-1]

        if last_candle_time != candle_time:
            last_candle_time = candle_time
            break

        time.sleep(1)


print(f"[Auto Trading Started] Strategy: {STRATEGY_NAME}, Executor: {EXECUTOR_TYPE}, Interval: {INTERVAL}")

while not stop_signal:
    try:
        df = executor.fetch_ohlcv(TICKER, interval=INTERVAL).tail(1000)
        price = df.iloc[-1]['close']
        last_candle_time = df.index[-1]
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Current Price: {price:,.0f} KRW")

        # BUY LOGIC
        should_buy, buy_strength = strategy.should_buy(df)
        if should_buy:
            krw_balance = executor.get_krw()
            amount_krw = strategy.buy_amount(krw_balance, price, buy_strength)
            if amount_krw >= 5000:
                executor.buy(TICKER, amount_krw)

        # SELL LOGIC
        context = {
            "current_price": price,
            "avg_buy_price": executor.get_avg_buy_price(TICKER),
            "btc_balance": executor.get_btc(),
        }

        should_sell, reason, sell_strength = strategy.should_sell(df, context)
        if should_sell:
            btc_balance = context["btc_balance"]
            amount_btc = strategy.sell_amount(btc_balance, price, sell_strength)
            if amount_btc >= 0.0001:
                print(f">> Selling {amount_btc:.8f} BTC due to reason: {reason} (strength: {sell_strength:.2f})")
                executor.sell(TICKER, amount_btc)

    except Exception as e:
        print("[Error occurred]", e)

    wait_until_next_interval(INTERVAL_SECONDS)

print("[Auto Trading Stopped]")
