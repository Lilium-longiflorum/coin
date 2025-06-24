import pandas as pd
from strategies.base import Strategy

class Backtester:
    def __init__(self, strategy: Strategy, df: pd.DataFrame, initial_cash: float = 1_000_000,
                 fee_rate: float = 0.0005):
        self.strategy = strategy
        self.df = df.copy()
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.position = 0.0  # BTC 보유량
        self.fee_rate = fee_rate
        self.trade_log = []

    def run(self):
        for i in range(len(self.df)):
            window = self.df.iloc[:i+1]
            current_price = self.df.iloc[i]['close']

            context = {
                "current_price": current_price,
                "avg_buy_price": self._get_avg_buy_price(),
                "btc_balance": self.position
            }

            # SELL
            should_sell, reason, sell_strength = self.strategy.should_sell(window, context)
            if should_sell and self.position > 0:
                amount_btc = self.strategy.sell_amount(self.position, current_price, sell_strength)
                proceeds = amount_btc * current_price * (1 - self.fee_rate)
                self.cash += proceeds
                self.position -= amount_btc
                self._log_trade(i, "SELL", current_price, amount_btc, reason)
                continue

            # BUY
            should_buy, buy_strength = self.strategy.should_buy(window)
            if should_buy and self.cash > 0:
                amount_krw = self.strategy.buy_amount(self.cash, current_price, buy_strength)
                amount_krw = min(amount_krw, self.cash)
                amount_btc = (amount_krw * (1 - self.fee_rate)) / current_price
                self.cash -= amount_krw
                self.position += amount_btc
                self._log_trade(i, "BUY", current_price, amount_btc, "strategy_signal")

        return self._summary()

    def _get_avg_buy_price(self):
        buys = [t for t in self.trade_log if t['type'] == 'BUY']
        total_cost = sum(t['price'] * t['amount'] for t in buys)
        total_volume = sum(t['amount'] for t in buys)
        if total_volume == 0:
            return 0.0
        return total_cost / total_volume

    def _log_trade(self, idx, trade_type, price, amount, reason):
        self.trade_log.append({
            "timestamp": self.df.index[idx],
            "type": trade_type,
            "price": price,
            "amount": amount,
            "reason": reason
        })

    def _summary(self):
        from backtest.metrics import compute_metrics

        final_price = self.df.iloc[-1]['close']
        total_value = self.cash + self.position * final_price
        profit = total_value - self.initial_cash
        roi = (profit / self.initial_cash) * 100

        metrics = compute_metrics(self.trade_log, self.initial_cash, final_price)
        metrics.update({
            "final_value": round(total_value, 2),
            "profit": round(profit, 2),
            "roi_percent": round(roi, 2),
            "num_trades": len(self.trade_log),
            "trade_log": self.trade_log
        })
        return metrics
