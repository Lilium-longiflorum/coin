import pyupbit
from strategies import get_strategy
from backtest.backtester import Backtester

# 1. 데이터 로딩
df = pyupbit.get_ohlcv("KRW-BTC", interval="minute60", count=1440)

# 2. 전략 + 백테스터 초기화
strategy = get_strategy("rsi")
backtester = Backtester(strategy, df, initial_cash=600_000)

# 3. 실행
result = backtester.run()

# 4. 결과 출력
print("Backtest Summary:")
for key, value in result.items():
    if key != "trade_log":
        print(f"{key:>16}: {value}")
