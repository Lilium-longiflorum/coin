import pandas as pd
from strategies.base import Strategy
from utils.stop_loss import StopLossDetector
import config

class RSIStrategy(Strategy):
    def __init__(self, period=14, oversold=30, overbought=70, max_len=1000):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.max_len = max_len
        self.last_rsi = None
        self.last_buy_strength = 0.0
        self.last_sell_strength = 0.0
        self.stop_loss_detector = StopLossDetector()

    def compute_rsi(self, series: pd.Series) -> pd.Series:
        delta = series.diff()
        gain = delta.where(delta > 0, 0).rolling(window=self.period).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=self.period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def safe_rsi(self, series: pd.Series) -> float | None:
        try:
            series = series.tail(self.max_len)
            rsi = self.compute_rsi(series)
            latest = rsi.iloc[-1]
            if pd.isna(latest):
                return None
            self.last_rsi = latest
            return latest
        except Exception as e:
            print(f"[RSI ERROR] {e}")
            return None

    def should_buy(self, df: pd.DataFrame) -> tuple[bool, float]:
        close_series = df["close"].tail(self.max_len)
        rsi_value = self.safe_rsi(close_series)
        if rsi_value is None:
            return False, 0.0

        if rsi_value < self.oversold:
            # 강도는 oversold 기준에서 얼마나 더 낮은지에 따라
            strength = min(1.0, (self.oversold - rsi_value) / 20)
            self.last_buy_strength = strength
            return True, strength
        return False, 0.0

    def should_sell(self, df: pd.DataFrame, context: dict) -> tuple[bool, str, float]:
        current_price = context["current_price"]
        avg_buy_price = context["avg_buy_price"]
        profit = ((current_price - avg_buy_price) / avg_buy_price * 100) if avg_buy_price > 0 else 0

        # 익절
        if profit >= config.PROFIT_THRESHOLD:
            if profit >= config.MIN_PROFIT_TO_SELL:
                return True, "take_profit", 1.0
            else:
                return False, "none", 0.0

        # 손절
        close_series = df["close"].tail(10)
        if self.stop_loss_detector.should_stop_loss(close_series):
            return True, "sharp_decline", 1.0

        # RSI 기반 전략 매도 (과매수 영역)
        close_series = df["close"].tail(self.max_len)
        rsi_value = self.safe_rsi(close_series)
        if rsi_value is None:
            return False, "none", 0.0

        if rsi_value > self.overbought:
            if profit >= config.MIN_PROFIT_TO_SELL:
                strength = min(1.0, (rsi_value - self.overbought) / 20)
                self.last_sell_strength = strength
                return True, "strategy_signal", strength
            else:
                return False, "none", 0.0

        return False, "none", 0.0

    def buy_amount(self, krw_balance: float, current_price: float, strength: float = None) -> float:
        strength = strength if strength is not None else self.last_buy_strength
        return min(krw_balance, 30000.0 * strength)

    def sell_amount(self, btc_balance: float, current_price: float, strength: float = None) -> float:
        strength = strength if strength is not None else self.last_sell_strength
        return btc_balance * strength
