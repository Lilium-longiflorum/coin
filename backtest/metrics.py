import pandas as pd

def compute_metrics(trade_log: list, initial_cash: float, final_price: float):
    df = pd.DataFrame(trade_log)
    if df.empty:
        return {
            "mdd_percent": 0.0,
            "win_rate_percent": 0.0
        }

    equity_curve = []
    cash = initial_cash
    btc = 0.0

    for _, row in df.iterrows():
        if row['type'] == 'BUY':
            cash -= row['price'] * row['amount']
            btc += row['amount']
        else:
            cash += row['price'] * row['amount']
            btc -= row['amount']
        total = cash + btc * final_price
        equity_curve.append(total)

    equity_series = pd.Series(equity_curve)
    peak = equity_series.cummax()
    drawdown = (equity_series - peak) / peak
    mdd = drawdown.min() * 100

    # 승률 계산
    wins = 0
    total = 0
    for i in range(1, len(df)):
        if df.iloc[i]['type'] == 'SELL' and df.iloc[i - 1]['type'] == 'BUY':
            buy_price = df.iloc[i - 1]['price']
            sell_price = df.iloc[i]['price']
            if sell_price > buy_price:
                wins += 1
            total += 1

    win_rate = (wins / total * 100) if total > 0 else 0.0

    return {
        "mdd_percent": round(mdd, 2),
        "win_rate_percent": round(win_rate, 2)
    }