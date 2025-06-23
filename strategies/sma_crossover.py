from strategies.base import Strategy
import pandas as pd
import config

class SMACrossoverStrategy(Strategy):
    def __init__(self, short_window=5, long_window=20, max_len=1000):
        self.short_window = short_window
        self.long_window = long_window
        self.max_len = max_len

    def compute_moving_averages(self, close_series: pd.Series):
        short_ma = close_series.rolling(window=self.short_window).mean()
        long_ma = close_series.rolling(window=self.long_window).mean()
        return short_ma, long_ma

    def should_buy(self, df: pd.DataFrame) -> bool:
        close = df["close"].tail(self.max_len)

        try:
            short_ma, long_ma = self.compute_moving_averages(close)
            if len(short_ma) < 2 or len(long_ma) < 2:
                return False

            return (
                short_ma.iloc[-2] < long_ma.iloc[-2] and
                short_ma.iloc[-1] > long_ma.iloc[-1]
            )
        except Exception as e:
            print(f"[SMA BUY ERROR] {e}")
            return False

    def should_sell(self, df: pd.DataFrame, context: dict) -> tuple[bool, str]:
        current_price = context["current_price"]
        avg_buy_price = context["avg_buy_price"]
        profit = ((current_price - avg_buy_price) / avg_buy_price * 100) if avg_buy_price else 0

        # 1. 익절 조건
        if profit >= config.PROFIT_THRESHOLD:
            if profit >= config.MIN_PROFIT_TO_SELL:
                print(">> Strategy: take profit")
                return True, "take_profit"
            else:
                print(">> Strategy: not selling — profit below fee-adjusted minimum")
                return False, "none"

        # 2. 손절 조건
        elif profit <= config.LOSS_THRESHOLD:
            print(">> Strategy: stop loss")
            return True, "stop_loss"

        # 3. 전략 신호 조건 (SMA 데드크로스) + 수익률 확인
        close = df["close"].tail(self.max_len)
        try:
            short_ma, long_ma = self.compute_moving_averages(close)
            if len(short_ma) < 2 or len(long_ma) < 2:
                return False, "none"

            if short_ma.iloc[-2] > long_ma.iloc[-2] and short_ma.iloc[-1] < long_ma.iloc[-1]:
                if profit >= config.MIN_PROFIT_TO_SELL:
                    print(">> Strategy: selling due to SMA dead cross")
                    return True, "strategy_signal"
                else:
                    print(">> Strategy: signal ignored — profit below fee-adjusted minimum")
                    return False, "none"

        except Exception as e:
            print(f"[SMA SELL ERROR] {e}")
            return False, "none"

        # 4. 아무 조건도 해당되지 않음
        return False, "none"
