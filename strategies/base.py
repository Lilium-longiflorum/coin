from abc import ABC, abstractmethod
import pandas as pd

class Strategy(ABC):
    @abstractmethod
    def should_buy(self, df: pd.DataFrame) -> tuple[bool, float]:
        """
        Decide whether to buy based on the given price data.

        Returns:
            (should_buy: bool, strength: float)
            strength ∈ [0.0, 1.0]
        """
        pass

    @abstractmethod
    def should_sell(self, df: pd.DataFrame, context: dict) -> tuple[bool, str, float]:
        """
        Decide whether to sell based on the given price data and context.

        Returns:
            (should_sell: bool, reason: str, strength: float)
            reason ∈ {"take_profit", "stop_loss", "strategy_signal", "none"}
        """
        pass

    def buy_amount(self, krw_balance: float, current_price: float, strength: float = 1.0) -> float:
        """
        Return the amount of KRW to use for buying, scaled by strength.
        Default: fixed 10,000 KRW × strength.
        """
        return krw_balance * strength

    def sell_amount(self, btc_balance: float, current_price: float, strength: float = 1.0) -> float:
        """
        Return the amount of BTC to sell, scaled by strength.
        Default: sell all × strength.
        """
        return btc_balance * strength
