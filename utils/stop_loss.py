import pandas as pd
import config

class StopLossDetector:
    def __init__(self, sharp_drop_threshold: float = config.LOSS_THRESHOLD, lookback: int = 3):
        """
        :param sharp_drop_threshold: % 기준 급락 임계치 (e.g., -3.0은 -3% 이상 하락)
        :param lookback: 최근 몇 개 캔들 구간에서의 낙폭을 볼지
        """
        self.sharp_drop_threshold = sharp_drop_threshold
        self.lookback = lookback

    def is_sharp_decline(self, close_series: pd.Series) -> bool:
        """
        급격한 하락 여부를 판단
        최근 lookback 기간 동안의 하락률이 sharp_drop_threshold 이하이면 True
        """
        if len(close_series) < self.lookback:
            return False

        recent = close_series.tail(self.lookback)
        drop_pct = (recent.iloc[-1] - recent.iloc[0]) / recent.iloc[0] * 100
        return drop_pct <= self.sharp_drop_threshold

    def should_stop_loss(self, close_series: pd.Series) -> bool:
        """
        외부 호출용 인터페이스: 급격한 하락 기준만 판단
        """
        return self.is_sharp_decline(close_series)
