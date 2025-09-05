import pyupbit
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def run_hybrid_backtest(ticker="KRW-BTC", initial_capital=1000000, fee_rate=0.0005):
    """
    골든크로스(장기 필터)와 변동성 돌파(단기 신호)를 결합한 하이브리드 전략 백테스팅.
    """
    print("🚀 하이브리드 전략 백테스팅 시작...")
    print("장기 필터: 15/80일 MA (일봉) | 단기 신호: 변동성 돌파 k=0.5 (4시간봉)")

    # 1. 데이터 준비 (일봉 & 4시간봉)
    df_daily = pyupbit.get_ohlcv(ticker, interval="day", count=500)
    df_4h = pyupbit.get_ohlcv(ticker, interval="minute240", count=500*6)
    if df_daily is None or df_4h is None:
        print("❌ 데이터 로드 실패")
        return

    # 2. 장기 추세 필터 계산 (일봉 기준)
    df_daily['short_ma'] = df_daily['close'].rolling(window=15).mean()
    df_daily['long_ma'] = df_daily['close'].rolling(window=80).mean()
    df_daily['regime'] = np.where(df_daily['short_ma'] > df_daily['long_ma'], 'GC', 'DC')
    
    # 4시간봉 데이터에 장기 추세 정보 결합
    regime_series = df_daily['regime'].reindex(df_4h.index, method='ffill')
    df_4h['regime'] = regime_series

    # 3. 단기 진입/청산 신호 계산 (4시간봉 기준)
    k = 0.5 # 변동성 돌파 k값
    df_4h['range'] = (df_4h['high'] - df_4h['low']).shift(1)
    df_4h['target'] = df_4h['open'] + df_4h['range'] * k
    
    # 4. 모의 투자 실행
    df_4h['position'] = 'cash'  # cash, holding
    df_4h['capital'] = initial_capital

    for i in range(1, len(df_4h)):
        # 이전 상태를 기본으로 설정
        df_4h.loc[df_4h.index[i], 'position'] = df_4h.loc[df_4h.index[i-1], 'position']
        df_4h.loc[df_4h.index[i], 'capital'] = df_4h.loc[df_4h.index[i-1], 'capital']

        # 현재 상태 변수
        current_regime = df_4h.loc[df_4h.index[i], 'regime']
        current_high = df_4h.loc[df_4h.index[i], 'high']
        target_price = df_4h.loc[df_4h.index[i], 'target']
        current_position = df_4h.loc[df_4h.index[i], 'position']
        
        # 매수 조건: (골든크로스 상태) AND (목표가 돌파) AND (현금 보유)
        if current_regime == 'GC' and current_high > target_price and current_position == 'cash':
            df_4h.loc[df_4h.index[i], 'position'] = 'holding'
            # 매수 시점의 자본 변화는 매도 시점에 정산 (수수료 계산 간소화)

        # 매도 조건: (데드크로스 상태) AND (자산 보유)
        elif current_regime == 'DC' and current_position == 'holding':
            df_4h.loc[df_4h.index[i], 'position'] = 'cash'
            
            # 수익률 계산
            entry_row = df_4h[df_4h.index < df_4h.index[i]].query("position == 'cash'").index[-1]
            entry_price = df_4h.loc[entry_row, 'target']
            exit_price = df_4h.loc[df_4h.index[i], 'open']
            
            profit = (exit_price / entry_price) * (1 - fee_rate)**2
            df_4h.loc[df_4h.index[i], 'capital'] *= profit

    # 최종 수익률 계산 (마지막까지 보유중인 경우)
    if df_4h['position'].iloc[-1] == 'holding':
        entry_row = df_4h.query("position == 'cash'").index[-1]
        entry_price = df_4h.loc[entry_row, 'target']
        exit_price = df_4h['close'].iloc[-1]
        profit = (exit_price / entry_price)
        df_4h.loc[df_4h.index[-1], 'capital'] *= profit

    df_4h['cumulative_return'] = df_4h['capital'] / initial_capital
    
    # 5. 성과 분석
    final_capital = df_4h['capital'].iloc[-1]
    total_return = (final_capital / initial_capital) - 1
    
    df_4h['peak'] = df_4h['cumulative_return'].cummax()
    drawdown = (df_4h['cumulative_return'] - df_4h['peak']) / df_4h['peak']
    mdd = drawdown.min()

    buy_and_hold_return = (df_4h['close'].iloc[-1] / df_4h['close'].iloc[0]) - 1

    print("\n✅ 백테스팅 완료!")
    print("---------------------------------")
    print(f"최종 자산: {final_capital:,.0f}원")
    print(f"누적 수익률: {total_return*100:.2f}%")
    print(f"단순 보유 수익률: {buy_and_hold_return*100:.2f}%")
    print(f"최대 낙폭 (MDD): {mdd*100:.2f}%")
    print("---------------------------------")

    # 6. 시각화
    plt.figure(figsize=(14, 7))
    plt.plot(df_4h.index, df_4h['cumulative_return'], label="Hybrid Strategy")
    plt.plot(df_4h.index, df_4h['close'] / df_4h['close'].iloc[0], label="Buy and Hold")
    plt.title('Hybrid Strategy Performance (GC Filter + VB Signal)')
    plt.legend()
    plt.grid()
    plt.savefig('hybrid_backtest_result.png')
    print("📈 백테스팅 결과가 'hybrid_backtest_result.png' 파일로 저장되었습니다.")

if __name__ == '__main__':
    run_hybrid_backtest()
