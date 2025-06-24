import pandas as pd
from strategies.base import Strategy
from utils.stop_loss import StopLossDetector
import config

class SMACrossoverStrategy(Strategy):
    def __init__(self, short_window=5, long_window=20, max_len=1000):
        self.short_window = short_window
        self.long_window = long_window
        self.max_len = max_len
        self.last_buy_strength = 0.0
        self.last_sell_strength = 0.0
        self.stop_loss_detector = StopLossDetector()

    def compute_moving_averages(self, close_series: pd.Series):
        short_ma = close_series.rolling(window=self.short_window).mean()
        long_ma = close_series.rolling(window=self.long_window).mean()
        return short_ma, long_ma

    def should_buy(self, df: pd.DataFrame) -> tuple[bool, float]:
        close = df["close"].tail(self.max_len)

        try:
            short_ma, long_ma = self.compute_moving_averages(close)
            if len(short_ma) < 2 or len(long_ma) < 2:
                return False, 0.0

            prev_cross = short_ma.iloc[-2] - long_ma.iloc[-2]
            curr_cross = short_ma.iloc[-1] - long_ma.iloc[-1]

            if prev_cross < 0 and curr_cross > 0:
                # 강도 계산: 교차 폭 대비 long_ma 기준 상대 비율
                strength = min(1.0, abs(curr_cross) / long_ma.iloc[-1])
                self.last_buy_strength = strength
                return True, strength

        except Exception as e:
            print(f"[SMA BUY ERROR] {e}")

        return False, 0.0

    def should_sell(self, df: pd.DataFrame, context: dict) -> tuple[bool, str, float]:
        current_price = context["current_price"]
        avg_buy_price = context["avg_buy_price"]
        profit = ((current_price - avg_buy_price) / avg_buy_price * 100) if avg_buy_price else 0

        # 1. 익절
        if profit >= config.PROFIT_THRESHOLD:
            if profit >= config.MIN_PROFIT_TO_SELL:
                return True, "take_profit", 1.0
            else:
                return False, "none", 0.0

        close = df["close"].tail(self.max_len)

        # 2. 손절: 급격한 하락 감지
        if self.stop_loss_detector.should_stop_loss(close):
            return True, "sharp_decline", 1.0

        # 3. 데드크로스
        try:
            short_ma, long_ma = self.compute_moving_averages(close)
            if len(short_ma) < 2 or len(long_ma) < 2:
                return False, "none", 0.0

            prev_cross = short_ma.iloc[-2] - long_ma.iloc[-2]
            curr_cross = short_ma.iloc[-1] - long_ma.iloc[-1]

            if prev_cross > 0 and curr_cross < 0:
                if profit >= config.MIN_PROFIT_TO_SELL:
                    strength = min(1.0, abs(curr_cross) / long_ma.iloc[-1])
                    self.last_sell_strength = strength
                    return True, "strategy_signal", strength

        except Exception as e:
            print(f"[SMA SELL ERROR] {e}")

        return False, "none", 0.0


    def buy_amount(self, krw_balance: float, current_price: float, strength: float = None) -> float:
        strength = strength if strength is not None else self.last_buy_strength
        return min(krw_balance, 30000.0 * strength)

    def sell_amount(self, btc_balance: float, current_price: float, strength: float = None) -> float:
        strength = strength if strength is not None else self.last_sell_strength
        return btc_balance * strength
