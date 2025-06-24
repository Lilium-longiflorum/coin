import pandas as pd
import config

class StopLossDetector:
    candle_interval_minutes: int = 1

    def __init__(self, sharp_drop_threshold: float = config.LOSS_THRESHOLD, lookback_minutes: int = 15):
        """
        :param sharp_drop_threshold: % 기준 급락 임계치 (예: -3.0은 -3% 이상 하락)
        :param lookback_minutes: 손절 판단 기준 시간 (분 단위)
        """
        self.sharp_drop_threshold = sharp_drop_threshold
        self.lookback_minutes = lookback_minutes

    def compute_lookback(self) -> int:
        """
        클래스 변수에 설정된 candle_interval_minutes를 기준으로 사용할 봉 개수 계산
        :return: 사용할 봉 개수 (최소 2 이상)
        """
        return max(2, self.lookback_minutes // StopLossDetector.candle_interval_minutes)

    def is_sharp_decline(self, close_series: pd.Series) -> bool:
        """
        급격한 하락 여부 판단
        :param close_series: 종가 시계열
        :return: 급격한 하락 감지 여부
        """
        lookback = self.compute_lookback()
        if len(close_series) < lookback:
            return False

        recent = close_series.tail(lookback)
        drop_pct = (recent.iloc[-1] - recent.iloc[0]) / recent.iloc[0] * 100
        return drop_pct <= self.sharp_drop_threshold

    def should_stop_loss(self, close_series: pd.Series) -> bool:
        """
        외부 호출용 손절 판단 메서드
        :param close_series: 종가 시계열
        :return: 손절 여부
        """
        return self.is_sharp_decline(close_series)
