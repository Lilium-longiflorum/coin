from abc import ABC, abstractmethod
import pandas as pd

class Executor(ABC):
    @abstractmethod
    def fetch_ohlcv(self, ticker: str, interval: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_current_price(self, ticker: str) -> float:
        pass

    @abstractmethod
    def get_krw(self) -> float:
        pass

    @abstractmethod
    def get_btc(self) -> float:
        pass

    @abstractmethod
    def buy(self, ticker: str, amount_krw: float):
        pass

    @abstractmethod
    def sell(self, ticker: str, amount_btc: float):
        pass

    @abstractmethod
    def get_avg_buy_price(self, ticker: str) -> float:
        pass