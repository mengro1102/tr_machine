import pyupbit
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd

def SMA(array, n):
    """Simple moving average"""
    return pd.Series(array).rolling(n).mean()

class GoldenCross(Strategy):
    # 전략에 사용할 변수 정의
    short_ma_period = 15
    long_ma_period = 80

    def init(self):
        # 전략에 사용할 지표들을 미리 계산
        # self.I() 함수는 미래 데이터를 보지 않도록 안전하게 지표를 계산해줌
        self.short_ma = self.I(SMA, self.data.Close, self.short_ma_period)
        self.long_ma = self.I(SMA, self.data.Close, self.long_ma_period)

    def next(self):
        # 골든크로스 발생 및 현재 포지션이 없을 경우, 자산의 95%를 매수
        if crossover(self.short_ma, self.long_ma) and not self.position:
            self.buy(size=0.95)

        # 데드크로스 발생 및 현재 포지션이 있을 경우, 전량 매도
        elif crossover(self.long_ma, self.short_ma) and self.position:
            self.position.close()

def run_validation():
    """
    backtesting.py 라이브러리를 사용하여 골든크로스 전략을 교차 검증합니다.
    """
    print("🔬 전문 라이브러리(`backtesting.py`)를 사용한 교차 검증 시작...")

    # 1. 데이터 준비 (라이브러리 형식에 맞게 컬럼명 변경)
    df = pyupbit.get_ohlcv("KRW-BTC", interval="day", count=500)
    
    # 불필요한 'value' 컬럼 삭제
    df = df.drop(columns=['value'])
    
    # backtesting.py가 요구하는 형식으로 컬럼명 변경
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    if df is None:
        print("❌ 데이터 로드 실패")
        return

    # 2. 백테스팅 실행 (초기 자본금 상향)
    bt = Backtest(df, GoldenCross,
                  cash=100_000_000, commission=.0005)
    
    stats = bt.run()
    
    # 3. 결과 출력
    print("\n✅ 교차 검증 완료!")
    print("-------------------------------------------")
    print("📊 `backtesting.py` 라이브러리 분석 결과 📊")
    print(stats)
    print("-------------------------------------------")
    
    # 4. 상세 리포트 및 그래프 저장
    # 동일한 이름의 파일이 있으면 덮어쓰지 않으므로, 실행 전 기존 파일 삭제 권장
    try:
        bt.plot(filename='bt_validation_report.html', open_browser=False)
        print("📈 상세 분석 리포트가 'bt_validation_report.html' 파일로 저장되었습니다.")
    except Exception as e:
        print(f"❌ 리포트 생성 실패: {e}")
        print("   (이전 리포트 파일을 삭제하고 다시 시도해 보세요.)")


if __name__ == '__main__':
    run_validation()
