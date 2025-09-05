import pyupbit
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def run_backtest(ticker="KRW-BTC", interval="day", short_window=20, long_window=60, initial_capital=1000000, fee_rate=0.0005):
    """
    골든크로스/데드크로스 전략 백테스팅을 실행하고 결과를 시각화합니다.
    """
    print(f"🚀 '{ticker}' 종목 골든크로스 전략 백테스팅 시작...")
    print(f"단기 MA: {short_window}일, 장기 MA: {long_window}일, 초기자본: {initial_capital:,.0f}원")

    # 1. 데이터 준비 (최근 1년치)
    df = pyupbit.get_ohlcv(ticker, interval=interval, count=365 + long_window)
    if df is None:
        print("❌ 데이터 로드 실패")
        return None

    # 2. 전략 구현
    df['short_ma'] = df['close'].rolling(window=short_window).mean()
    df['long_ma'] = df['close'].rolling(window=long_window).mean()
    df = df.iloc[long_window:].copy()
    df['position'] = np.where(df['short_ma'] > df['long_ma'], 1, 0)
    df['signal'] = df['position'].diff()

    # 3. 모의 투자 실행
    df['cash'] = 0.0
    df['holding'] = 0.0
    df.loc[df.index[0], 'cash'] = initial_capital

    for i in range(1, len(df)):
        prev_row = df.iloc[i-1]
        current_row = df.iloc[i]
        df.loc[df.index[i], 'cash'] = prev_row['cash']
        df.loc[df.index[i], 'holding'] = prev_row['holding']

        if df.loc[df.index[i], 'signal'] == 1: # 매수
            buy_amount = prev_row['cash']
            df.loc[df.index[i], 'holding'] = (buy_amount / current_row['close']) * (1 - fee_rate)
            df.loc[df.index[i], 'cash'] = 0
        elif df.loc[df.index[i], 'signal'] == -1: # 매도
            sell_amount = prev_row['holding'] * current_row['close']
            df.loc[df.index[i], 'cash'] = sell_amount * (1 - fee_rate)
            df.loc[df.index[i], 'holding'] = 0

    df['total'] = df['cash'] + df['holding'] * df['close']
    
    # 4. 성과 분석
    final_total = df['total'].iloc[-1]
    total_return = (final_total / initial_capital) - 1
    df['peak'] = df['total'].cummax()
    df['drawdown'] = (df['total'] - df['peak']) / df['peak']
    mdd = df['drawdown'].min()

    # Buy and Hold 전략 성과
    buy_and_hold_return = (df['close'].iloc[-1] / df['close'].iloc[0]) - 1

    results = {
        "final_capital": final_total,
        "total_return_pct": total_return * 100,
        "buy_and_hold_pct": buy_and_hold_return * 100,
        "mdd_pct": mdd * 100,
    }
    
    print("\n✅ 백테스팅 완료!")
    print("---------------------------------")
    print(f"최종 자산: {results['final_capital']:,.0f}원")
    print(f"누적 수익률: {results['total_return_pct']:.2f}%")
    print(f"단순 보유 수익률: {results['buy_and_hold_pct']:.2f}%")
    print(f"최대 낙폭 (MDD): {results['mdd_pct']:.2f}%")
    print("---------------------------------")
    
    # 5. 시각화
    plt.figure(figsize=(14, 7))
    plt.plot(df.index, df['total'] / initial_capital, label="Golden Cross Strategy")
    plt.plot(df.index, df['close'] / df['close'].iloc[0], label="Buy and Hold")
    plt.title(f'Strategy Performance ({ticker}) - {short_window}d/{long_window}d MA')
    plt.xlabel('Date')
    plt.ylabel('Normalized Return')
    plt.legend()
    plt.grid()
    plt.savefig('backtest_result.png')
    print("📈 백테스팅 결과가 'backtest_result.png' 파일로 저장되었습니다.")
    
    return results

if __name__ == '__main__':
    # 최적화된 파라미터(15, 80)로 백테스팅 실행
    run_backtest(ticker="KRW-BTC", short_window=15, long_window=80)