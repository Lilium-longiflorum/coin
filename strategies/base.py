from abc import ABC, abstractmethod
import pandas as pd

class Strategy(ABC):
    @abstractmethod
    def should_buy(self, df: pd.DataFrame) -> bool:
        """
        Decide whether to buy based on the given price data.
        """
        pass

    @abstractmethod
    def should_sell(self, df: pd.DataFrame, context: dict) -> tuple[bool, str]:
        """
        Decide whether to sell based on the given price data and context.

        Returns:
            (should_sell: bool, reason: str)
            reason ∈ {"take_profit", "stop_loss", "strategy_signal", "none"}
        """
        pass

    def buy_amount(self, krw_balance: float, current_price: float) -> float:
        """
        Return the amount of KRW to use for buying.
        Override this method to implement position sizing logic.
        Default: fixed 10,000 KRW.
        """
        return 10000.0

    def sell_amount(self, btc_balance: float, current_price: float) -> float:
        """
        Return the amount of BTC to sell.
        Override this method to implement position sizing logic.
        Default: sell all.
        """
        return btc_balance
