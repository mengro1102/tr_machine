import pyupbit
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time

def run_vb_backtest(ticker="KRW-BTC", k=0.5, initial_capital=1000000, fee_rate=0.0005):
    """
    변동성 돌파 전략 백테스팅을 실행합니다. (분봉 데이터 사용)
    """
    # 1. 데이터 준비 (최근 100일치 240분봉 데이터)
    df = pyupbit.get_ohlcv(ticker, interval="minute240", count=100*6) # 240분봉은 하루에 6개
    if df is None:
        return None

    # 2. 전략 구현
    df['noise'] = 1 - abs(df['open'] - df['close']) / (df['high'] - df['low'])
    df['range'] = (df['high'] - df['low']).shift(1)
    df['target'] = df['open'] + df['range'] * k
    
    # 3. 모의 투자 실행
    df['holding'] = False
    df['return'] = 1.
    
    for i in range(1, len(df)):
        # 목표가 돌파 시 매수
        if df.iloc[i]['high'] > df.iloc[i]['target']:
            fee = 1 - fee_rate
            # 다음 캔들 시가에 매도
            buy_price = df.iloc[i]['target']
            sell_price = df.iloc[i+1]['open'] if i + 1 < len(df) else df.iloc[i]['close']
            df.loc[df.index[i], 'return'] = (sell_price / buy_price) * fee * fee
            df.loc[df.index[i], 'holding'] = True

    df['cumulative_return'] = df['return'].cumprod()
    final_capital = initial_capital * df['cumulative_return'].iloc[-1]
    
    return {
        "k_value": k,
        "final_capital": final_capital,
        "total_return_pct": (final_capital / initial_capital - 1) * 100,
        "df": df # 시각화를 위해 데이터프레임 반환
    }

def optimize_and_visualize():
    """
    최적의 k값을 찾고, 그 결과를 바탕으로 최종 백테스팅 및 시각화를 수행합니다.
    """
    print("📈 변동성 돌파 전략 최적화를 시작합니다... (k=0.1 ~ 1.0)")
    
    k_values = np.arange(0.1, 1.1, 0.1)
    results = []
    
    for k in k_values:
        print(f"--- k={k:.1f} 테스트 중 ---")
        result = run_vb_backtest(k=k)
        if result:
            results.append(result)
        time.sleep(1) # API 호출 제한 방지

    if not results:
        print("❌ 최적화 실패.")
        return

    # 최적 k값 찾기
    best_performance = max(results, key=lambda x: x['final_capital'])
    best_k = best_performance['k_value']
    
    print("\n\n✅ 최적화 완료!")
    print("-------------------------------------------")
    print(f"🏆 최적 K값: {best_k:.1f}")
    print(f"최종 자산: {best_performance['final_capital']:,.0f}원")
    print(f"누적 수익률: {best_performance['total_return_pct']:.2f}%")
    print("-------------------------------------------")

    # 최적 k값으로 최종 백테스팅 및 시각화
    print("\n📈 최적 K값으로 최종 백테스팅 및 시각화를 진행합니다...")
    final_result_df = best_performance['df']
    
    # Buy and Hold 전략 성과
    initial_price = final_result_df['open'].iloc[0]
    final_price = final_result_df['close'].iloc[-1]
    buy_and_hold_return = (final_price / initial_price)
    final_result_df['buy_and_hold'] = final_result_df['close'] / initial_price

    plt.figure(figsize=(14, 7))
    plt.plot(final_result_df.index, final_result_df['cumulative_return'], label=f"Volatility Breakout (k={best_k:.1f})")
    plt.plot(final_result_df.index, final_result_df['buy_and_hold'], label="Buy and Hold")
    plt.title(f'Volatility Breakout Strategy Performance (KRW-BTC)')
    plt.xlabel('Date')
    plt.ylabel('Normalized Return')
    plt.legend()
    plt.grid()
    plt.savefig('vb_backtest_result.png')
    print("📈 백테스팅 결과가 'vb_backtest_result.png' 파일로 저장되었습니다.")

if __name__ == '__main__':
    optimize_and_visualize()
