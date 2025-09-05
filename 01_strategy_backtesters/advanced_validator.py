from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import pyupbit

def SMA(array, n):
    """Simple moving average"""
    return pd.Series(array).rolling(n).mean()

def RSI(array, n):
    """Relative strength index"""
    gain = pd.Series(array).diff()
    loss = gain.copy()
    gain[gain < 0] = 0
    loss[loss > 0] = 0
    rs = gain.ewm(n).mean() / abs(loss.ewm(n).mean())
    return 100 - 100 / (1 + rs)

class GcRsiStrategy(Strategy):
    # 전략 파라미터 정의
    short_ma_period = 15
    long_ma_period = 80
    rsi_period = 14
    rsi_oversold_threshold = 30

    def init(self):
        # 지표 계산
        self.short_ma = self.I(SMA, self.data.Close, self.short_ma_period)
        self.long_ma = self.I(SMA, self.data.Close, self.long_ma_period)
        self.rsi = self.I(RSI, self.data.Close, self.rsi_period)

    def next(self):
        # 현재 시장 상태 정의
        is_gc_regime = self.short_ma[-1] > self.long_ma[-1]
        is_rsi_oversold = self.rsi[-1] < self.rsi_oversold_threshold
        
        # 매수 조건: (골든크로스 상태) AND (RSI 과매도) AND (미보유)
        if is_gc_regime and is_rsi_oversold and not self.position:
            self.buy(size=0.95)

        # 매도 조건: 데드크로스 발생 시 전량 매도
        if crossover(self.long_ma, self.short_ma) and self.position:
            self.position.close()

def run_advanced_validation():
    """
    골든크로스와 RSI를 결합한 하이브리드 전략을 검증합니다.
    """
    print("🔬 고급 전략(GC+RSI) 교차 검증 시작...")

    # 데이터 준비
    df = pyupbit.get_ohlcv("KRW-BTC", interval="day", count=500)
    df = df.drop(columns=['value'])
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    if df is None:
        print("❌ 데이터 로드 실패")
        return

    # 백테스팅 실행
    bt = Backtest(df, GcRsiStrategy,
                  cash=100_000_000, commission=.0005)
    
    stats = bt.run()
    
    print("\n✅ 교차 검증 완료!")
    print("-------------------------------------------")
    print("📊 고급 전략(GC+RSI) 분석 결과 📊")
    print(stats)
    print("-------------------------------------------")
    
    # 리포트 저장
    report_path = '04_reports/advanced_strategy_report.html'
    bt.plot(filename=report_path, open_browser=False)
    print(f"📈 상세 분석 리포트가 '{report_path}' 파일로 저장되었습니다.")


if __name__ == '__main__':
    run_advanced_validation()
