import asyncio
import websockets
import orjson
import uuid
from datetime import datetime

async def run_pro_analyzer(ticker="KRW-BTC"):
    """
    Upbit WebSocket 서버와 직접 통신하며 자동 재연결을 지원하는 실시간 호가창 분석기.
    """
    uri = "wss://api.upbit.com/websocket/v1"
    
    print("🚀 실시간 호가창 분석기를 시작합니다 (저지연, 자동 재연결 버전)...")
    print("분석 대상:", ticker)
    print("--------------------------------------------------")

    while True:
        try:
            async with websockets.connect(uri, ping_interval=60) as websocket:
                subscribe_msg = [
                    {"ticket": str(uuid.uuid4())},
                    {"type": "orderbook", "codes": [ticker]}
                ]
                await websocket.send(orjson.dumps(subscribe_msg))
                print("✅ Upbit WebSocket 서버에 직접 연결 및 구독 완료.")

                while True:
                    data = await websocket.recv()
                    orderbook_data = orjson.loads(data)
                    orderbook_units = orderbook_data.get('orderbook_units', [])
                    
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

        except websockets.exceptions.ConnectionClosed:
            print("\n🔌 WebSocket 연결이 끊어졌습니다.")
        except Exception as e:
            print(f"\n❌ 에러 발생: {e}")
        
        print("🔌 5초 후 재연결을 시도합니다...")
        await asyncio.sleep(5)


if __name__ == '__main__':
    try:
        asyncio.run(run_pro_analyzer())
    except KeyboardInterrupt:
        print("\n👋 분석기를 종료합니다.")