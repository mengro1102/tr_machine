import pyupbit
import config
import pandas as pd
import time

# -----------------------------------------------------------------------------
# 최적화된 전략 파라미터
# -----------------------------------------------------------------------------
SHORT_WINDOW = 15
LONG_WINDOW = 80
TICKER = "KRW-BTC"
FEE_RATE = 0.0005
INTERVAL = "day" # 일봉 기준

# -----------------------------------------------------------------------------
# 모의 투자 상태 변수
# -----------------------------------------------------------------------------
initial_capital = 1000000
cash = initial_capital
btc_balance = 0.0
position = "CASH" # "CASH" or "BTC"

def print_status(price, short_ma, long_ma):
    """현재 상태를 출력하는 함수"""
    print("--------------------------------------------------")
    print(f"현재 시간: {pd.Timestamp.now()}")
    print(f"현재 {TICKER} 가격: {price:,.0f} KRW")
    print(f"단기({SHORT_WINDOW}일) MA: {short_ma:,.0f} KRW")
    print(f"장기({LONG_WINDOW}일) MA: {long_ma:,.0f} KRW")
    print(f"현재 포지션: {position}")
    
    total_asset = cash + (btc_balance * price)
    print(f"현재 총 자산: {total_asset:,.0f} KRW")
    print(f"  - 보유 현금: {cash:,.0f} KRW")
    print(f"  - 보유 BTC: {btc_balance:.8f} BTC")
    print("--------------------------------------------------\n")


def run_trading_bot():
    """자동매매 봇을 실행합니다."""
    global cash, btc_balance, position
    
    print("🤖 최적화된 골든크로스 전략으로 모의 투자를 시작합니다.")
    print(f"전략: 단기 {SHORT_WINDOW}일 / 장기 {LONG_WINDOW}일")
    
    while True:
        try:
            # 1. 데이터 가져오기
            df = pyupbit.get_ohlcv(TICKER, interval=INTERVAL, count=LONG_WINDOW + 2)
            if df is None:
                print("데이터를 가져오지 못했습니다. 10초 후 재시도...")
                time.sleep(10)
                continue

            # 2. 전략 계산
            df['short_ma'] = df['close'].rolling(window=SHORT_WINDOW).mean()
            df['long_ma'] = df['close'].rolling(window=LONG_WINDOW).mean()
            
            # 최근 데이터 사용
            latest = df.iloc[-1]
            
            # 3. 신호 생성
            is_golden_cross = latest['short_ma'] > latest['long_ma']
            
            # 현재 가격
            current_price = pyupbit.get_current_price(TICKER)
            if current_price is None:
                print("현재가를 가져오지 못했습니다. 10초 후 재시도...")
                time.sleep(10)
                continue

            # 상태 출력
            print_status(current_price, latest['short_ma'], latest['long_ma'])

            # 4. 모의 주문 실행
            # 매수 상태가 아닌데 골든크로스 발생 -> 매수
            if position == "CASH" and is_golden_cross:
                buy_amount = cash
                btc_balance = (buy_amount / current_price) * (1 - FEE_RATE)
                cash = 0
                position = "BTC"
                print(f"🔥🔥🔥 [매수 실행] 골든크로스 발생! 🔥🔥🔥")
                print(f"{current_price:,.0f} KRW에 {btc_balance:.8f} BTC 매수")

            # 매수 상태인데 데드크로스 발생 -> 매도
            elif position == "BTC" and not is_golden_cross:
                sell_amount = btc_balance * current_price
                cash = sell_amount * (1 - FEE_RATE)
                btc_balance = 0
                position = "CASH"
                print(f"🥶🥶🥶 [매도 실행] 데드크로스 발생! 🥶🥶🥶")
                print(f"{current_price:,.0f} KRW에 {btc_balance:.8f} BTC 매도")
            
            else:
                print("... 포지션 유지 ...")

            # 1시간 대기
            print("\n다음 거래 신호까지 1시간 대기합니다...")
            time.sleep(3600)

        except Exception as e:
            print(f"❌ 에러 발생: {e}")
            print("10초 후 재시도...")
            time.sleep(10)

if __name__ == '__main__':
    run_trading_bot()