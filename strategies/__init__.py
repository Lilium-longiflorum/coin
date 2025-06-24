from strategies.rsi_strategy import RSIStrategy
from strategies.sma_crossover import SMACrossoverStrategy
from strategies.trend_filter import TrendFilterStrategy

def get_strategy(name: str):
    if name == "sma":
        return SMACrossoverStrategy()
    elif name == "rsi":
        return RSIStrategy()
    elif name == "trend":
        return TrendFilterStrategy()
    else:
        raise ValueError(f"Unknown strategy: {name}")
