from strategies.rsi_strategy import RSIStrategy
from strategies.sma_crossover import SMACrossoverStrategy

def get_strategy(name: str):
    if name == "sma":
        return SMACrossoverStrategy()
    elif name == "rsi":
        return RSIStrategy()
    else:
        raise ValueError(f"Unknown strategy: {name}")
