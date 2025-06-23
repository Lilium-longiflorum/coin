import pyupbit
import time
import csv
from datetime import datetime
from pathlib import Path
from executor.base_executor import Executor
import threading
import queue

class UpbitExecutor(Executor):
    def __init__(self, api_key, secret_key):
        self.upbit = pyupbit.Upbit(api_key, secret_key)
        self.order_queue = queue.Queue()
        self.checked_uuids = set()
        self._start_order_checker()

    def fetch_ohlcv(self, ticker, interval="minute1"):
        return pyupbit.get_ohlcv(ticker, interval=interval)

    def get_current_price(self, ticker):
        return pyupbit.get_current_price(ticker)

    def get_balance(self, currency):
        try:
            balances = self.upbit.get_balances()
            for b in balances:
                if b['currency'] == currency:
                    return float(b['balance'])
        except Exception as e:
            print(f"[Balance Error] {e}")
        return 0.0

    def get_avg_buy_price(self, ticker):
        try:
            balances = self.upbit.get_balances()
            currency = ticker.split("-")[1]  # e.g., "BTC" from "KRW-BTC"
            for b in balances:
                if b['currency'] == currency:
                    return float(b['avg_buy_price'])
        except Exception as e:
            print(f"[Avg Buy Price Error] {e}")
        return 0.0

    def get_krw(self):
        return self.get_balance("KRW")

    def get_btc(self):
        return self.get_balance("BTC")

    def buy(self, ticker, amount_krw):
        if amount_krw < 5000:
            print(f"[Buy Failed] Minimum order amount is 5000 KRW.")
            return None
        try:
            print(f"[Buy] {ticker} - {amount_krw:,.0f} KRW")
            result = self.upbit.buy_market_order(ticker, amount_krw)
            if result and 'uuid' in result:
                self.order_queue.put(("BUY", result['uuid'], ticker))
            return result
        except Exception as e:
            print(f"[Buy Error] {e}")
            return None

    def sell(self, ticker, amount_btc):
        if amount_btc < 0.0001:
            print(f"[Sell Failed] Minimum order quantity is 0.0001 BTC.")
            return None
        try:
            print(f"[Sell] {ticker} - {amount_btc:.8f} BTC")
            result = self.upbit.sell_market_order(ticker, amount_btc)
            if result and 'uuid' in result:
                self.order_queue.put(("SELL", result['uuid'], ticker))
            return result
        except Exception as e:
            print(f"[Sell Error] {e}")
            return None

    def _start_order_checker(self):
        def run():
            while True:
                try:
                    trade_type, uuid, ticker = self.order_queue.get(timeout=1)
                    self._process_order(uuid, trade_type, ticker)
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"[Async Order Check Error] {e}")

        threading.Thread(target=run, daemon=True).start()

    def _process_order(self, uuid, trade_type, ticker):
        if uuid in self.checked_uuids:
            return
        try:
            time.sleep(0.3)  # Rate limit
            order = self.upbit.get_order(uuid)
            if not order or order.get("state") != "done":
                self.order_queue.put((trade_type, uuid, ticker))  # Retry later
                return

            trades = order.get('trades', [])
            total_price = 0.0
            total_volume = 0.0
            for t in trades:
                price = float(t['price'])
                volume = float(t['volume'])
                total_price += price * volume
                total_volume += volume

            if total_volume > 0:
                if trade_type == "BUY":
                    self.log_trade("BUY", price, total_volume)
                elif trade_type == "SELL":
                    avg_price = self.get_avg_buy_price(ticker)
                    profit = ((price - avg_price) / avg_price * 100) if avg_price > 0 else 0.0
                    self.log_trade("SELL", price, total_volume, profit)

            self.checked_uuids.add(uuid)

        except Exception as e:
            print(f"[Order Process Error] UUID: {uuid}, Type: {trade_type} — {e}")

    def log_trade(self, trade_type, price, amount, profit=None):
        log_path = Path("logs")
        log_path.mkdir(exist_ok=True)
        file = log_path / "trade_log.csv"
        file_exists = file.exists()

        avg_price = self.get_avg_buy_price("KRW-BTC")
        total_btc = self.get_btc()
        total_krw = self.get_krw()

        try:
            with file.open("a", newline="") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow([
                        "timestamp", "type", "price", "amount",
                        "profit", "avg_buy_price", "total_btc", "total_krw"
                    ])
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    trade_type,
                    f"{price:,.0f}",
                    f"{amount:.8f}",
                    f"{profit:.2f}%" if profit is not None else "",
                    f"{avg_price:,.0f}",
                    f"{total_btc:.8f}",
                    f"{total_krw:,.0f}"
                ])
        except Exception as e:
            print(f"[Log Write Error] {e}")
