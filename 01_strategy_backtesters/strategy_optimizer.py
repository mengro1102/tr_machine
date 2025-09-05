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
    # 최적화할 파라미터 정의
    rsi_oversold_threshold = 30 # 기본값

    # 고정 파라미터
    short_ma_period = 15
    long_ma_period = 80
    rsi_period = 14

    def init(self):
        self.short_ma = self.I(SMA, self.data.Close, self.short_ma_period)
        self.long_ma = self.I(SMA, self.data.Close, self.long_ma_period)
        self.rsi = self.I(RSI, self.data.Close, self.rsi_period)

    def next(self):
        is_gc_regime = self.short_ma[-1] > self.long_ma[-1]
        is_rsi_oversold = self.rsi[-1] < self.rsi_oversold_threshold
        
        if is_gc_regime and is_rsi_oversold and not self.position:
            self.buy(size=0.95)

        if crossover(self.long_ma, self.short_ma) and self.position:
            self.position.close()

def run_optimizer():
    """
    GC+RSI 전략의 최적 RSI 진입점을 찾습니다.
    """
    print("🔬 GC+RSI 전략 최적화 시작...")

    df = pyupbit.get_ohlcv("KRW-BTC", interval="day", count=500)
    df = df.drop(columns=['value'])
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    if df is None:
        return

    bt = Backtest(df, GcRsiStrategy,
                  cash=100_000_000, commission=.0005)
    
    # 최적화 실행
    stats = bt.optimize(
        rsi_oversold_threshold=range(30, 51, 5), # 30, 35, 40, 45, 50
        maximize='Equity Final [$]', # 최종 자산을 기준으로 최적화
        constraint=lambda p: p.rsi_oversold_threshold > 0 # 제약 조건
    )
    
    print("\n✅ 최적화 완료!")
    print("-------------------------------------------")
    print("📊 최적 파라미터 및 결과 📊")
    print(stats)
    print("\n📈 최적 파라미터 상세:")
    print(stats._strategy)
    print("-------------------------------------------")
    
    report_path = '04_reports/strategy_optimization_report.html'
    bt.plot(filename=report_path, open_browser=False)
    print(f"📈 상세 분석 리포트가 '{report_path}' 파일로 저장되었습니다.")


if __name__ == '__main__':
    run_optimizer()
