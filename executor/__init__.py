## executor/__init__.py

from .upbit_executor import UpbitExecutor
from .mock_executor import MockExecutor
from config import API_KEY, SECRET_KEY

def get_executor(name: str):
    if name == "upbit":
        return UpbitExecutor(API_KEY, SECRET_KEY)
    elif name == "mock":
        return MockExecutor(start_krw=1_000_000)
    else:
        raise ValueError(f"Unknown executor type: {name}")