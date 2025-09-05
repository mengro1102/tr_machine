import pyupbit
import time
from datetime import datetime

def run_tick_analyzer(ticker="KRW-BTC"):
    """
    실시간으로 호가창 데이터를 받아 매수/매도 압력을 분석합니다. (재연결 기능 추가)
    """
    print("📈 실시간 호가창 분석기를 시작합니다...")
    print("분석 대상:", ticker)
    print("--------------------------------------------------")
    
    while True:
        websocket = None
        try:
            # WebSocket 연결
            websocket = pyupbit.WebSocketManager(type="orderbook", codes=[ticker])
            print("✅ WebSocket 서버에 연결되었습니다.")
            
            while True:
                # 데이터 수신
                data = websocket.get()
                orderbook_units = data.get('orderbook_units', [])
                
                if not orderbook_units:
                    continue

                total_bid_size = sum(unit['bid_size'] for unit in orderbook_units)
                total_ask_size = sum(unit['ask_size'] for unit in orderbook_units)
                
                total_volume = total_bid_size + total_ask_size
                bid_pressure = (total_bid_size / total_volume) * 100 if total_volume > 0 else 50
                ask_pressure = (total_ask_size / total_volume) * 100 if total_volume > 0 else 50

                current_price = orderbook_units[0]['ask_price']
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                print(f"\r[{now}] [현재가: {int(current_price):,} KRW] | 🟢 매수 압력: {bid_pressure:5.2f}% | 🔴 매도 압력: {ask_pressure:5.2f}%", end="")

        except KeyboardInterrupt:
            print("\n👋 분석기를 종료합니다.")
            break
        except Exception as e:
            print(f"\n❌ 에러 발생: {e}")
        finally:
            if websocket:
                websocket.terminate()
        
        print("\n🔌 5초 후 재연결을 시도합니다...")
        time.sleep(5)


if __name__ == '__main__':
    run_tick_analyzer()
