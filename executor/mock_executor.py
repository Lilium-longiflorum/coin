import pyupbit
from executor.base_executor import Executor
from datetime import datetime
import csv
from pathlib import Path

class MockExecutor(Executor):
    def __init__(self, start_krw=1_000_000):
        self.krw = start_krw
        self.btc = 0.0
        self.mock_uuid_counter = 0
        self.buy_uuids = set()
        self.checked_uuids = set()
        self.buy_records = {}  # uuid -> (price, amount)
        self.total_btc = 0.0
        self.total_krw = 0.0
        self.avg_buy_price_cache = 0.0

    def fetch_ohlcv(self, ticker, interval="minute1"):
        return pyupbit.get_ohlcv(ticker, interval=interval)

    def get_current_price(self, ticker):
        return pyupbit.get_current_price(ticker)

    def get_krw(self):
        return self.krw

    def get_btc(self):
        return self.btc

    def buy(self, ticker, amount_krw):
        price = self.get_current_price(ticker)
        if amount_krw > self.krw or amount_krw < 5000:
            return
        fee = amount_krw * 0.0005
        real_amount = (amount_krw - fee) / price
        self.krw -= amount_krw
        self.btc += real_amount

        # UUID 생성 및 저장
        self.mock_uuid_counter += 1
        uuid = f"mock-{self.mock_uuid_counter:04d}"
        self.buy_uuids.add(uuid)
        self.buy_records[uuid] = (price, real_amount)

        print(f"[Simulated Buy] {amount_krw:,.0f} KRW → {real_amount:.8f} BTC @ {price:,.0f} KRW")
        self.log_trade("BUY", price, real_amount)

    def sell(self, ticker, amount_btc):
        price = self.get_current_price(ticker)
        if amount_btc > self.btc or amount_btc < 0.0001:
            return
        fee = amount_btc * 0.0005
        real_amount = amount_btc - fee
        gain = real_amount * price
        profit = ((price - self.get_avg_buy_price(ticker)) / self.get_avg_buy_price(ticker)) * 100 if self.total_btc > 0 else 0.0
        self.btc -= amount_btc
        self.krw += gain
        print(f"[Simulated Sell] {amount_btc:.8f} BTC → {gain:,.0f} KRW @ {price:,.0f} KRW | Return: {profit:.2f}%")
        self.log_trade("SELL", price, amount_btc, profit)

    def log_trade(self, trade_type, price, amount, profit=None):
        log_path = Path("logs")
        log_path.mkdir(exist_ok=True)
        file = log_path / "trade_log.csv"
        file_exists = file.exists()

        # 평균가와 누적 금액은 최신 기준으로 추출
        avg_price = self.get_avg_buy_price("KRW-BTC")  # ticker는 고정되어 있다고 가정
        total_btc = self.total_btc
        total_krw = self.total_krw

        with file.open("a", newline="") as f:
            writer = csv.writer(f)

            # 헤더가 없으면 생성
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


    def update_avg_buy_price(self, ticker):
        new_uuids = self.buy_uuids - self.checked_uuids
        for uuid in new_uuids:
            price, volume = self.buy_records[uuid]
            self.total_krw += price * volume
            self.total_btc += volume
            self.checked_uuids.add(uuid)
        if self.total_btc > 0:
            self.avg_buy_price_cache = self.total_krw / self.total_btc

    def get_avg_buy_price(self, ticker):
        return self.avg_buy_price_cache
