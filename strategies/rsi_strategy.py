import pandas as pd
from strategies.base import Strategy
import config

class RSIStrategy(Strategy):
    def __init__(self, period=14, oversold=30, overbought=70, max_len=1000):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.max_len = max_len

    def compute_rsi(self, series: pd.Series) -> pd.Series:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def safe_rsi(self, series: pd.Series) -> float | None:
        try:
            series = series.tail(self.max_len)
            rsi = self.compute_rsi(series)
            latest = rsi.iloc[-1]
            if pd.isna(latest):
                return None
            return latest
        except Exception as e:
            print(f"[RSI ERROR] {e}")
            return None

    def should_buy(self, df: pd.DataFrame) -> bool:
        close_series = df["close"].tail(self.max_len)
        rsi_value = self.safe_rsi(close_series)
        if rsi_value is None:
            return False
        return rsi_value < self.oversold

    def should_sell(self, df: pd.DataFrame, context: dict) -> tuple[bool, str]:
        current_price = context["current_price"]
        avg_buy_price = context["avg_buy_price"]
        profit = ((current_price - avg_buy_price) / avg_buy_price) * 100 if avg_buy_price > 0 else 0

        # 1. 익절 조건
        if profit >= config.PROFIT_THRESHOLD:
            if profit >= config.MIN_PROFIT_TO_SELL:
                print(">> Strategy: Selling due to profit-taking condition")
                return True, "take_profit"
            else:
                print(">> Strategy: Not selling — profit below minimum threshold after fees")
                return False, "none"

        # 2. 손절 조건
        elif profit <= config.LOSS_THRESHOLD:
            print(">> Strategy: Selling due to stop-loss condition")
            return True, "stop_loss"

        # 3. RSI 기반 매도 조건 (과매수 영역에서 이탈) + 수익률 확인
        close_series = df["close"].tail(self.max_len)
        rsi_value = self.safe_rsi(close_series)
        if rsi_value is None:
            return False, "none"

        if rsi_value > self.overbought:
            if profit >= config.MIN_PROFIT_TO_SELL:
                print(">> Strategy: Selling due to RSI overbought condition")
                return True, "strategy_signal"
            else:
                print(">> Strategy: RSI signal ignored — profit below fee-adjusted minimum")
                return False, "none"

        # 4. 아무 조건도 해당되지 않음
        return False, "none"


