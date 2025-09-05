import pandas as pd
from local_backtest import run_backtest

def optimize_strategy():
    """
    다양한 이동평균 조합으로 백테스팅을 실행하여 최적의 파라미터를 찾습니다.
    """
    print("📈 전략 최적화를 시작합니다...")
    
    # 테스트할 파라미터 범위 설정
    short_windows = range(5, 31, 5)   # 5, 10, 15, 20, 25, 30
    long_windows = range(30, 101, 10) # 30, 40, 50, ..., 100

    results = []
    
    for short in short_windows:
        for long in long_windows:
            # 단기 < 장기인 경우에만 테스트
            if short >= long:
                continue
            
            print(f"\n--- 테스트 중: 단기={short}, 장기={long} ---")
            result = run_backtest(
                ticker="KRW-BTC", 
                short_window=short, 
                long_window=long,
                initial_capital=1000000,
                fee_rate=0.0005
            )
            
            if result:
                results.append({
                    "short_window": short,
                    "long_window": long,
                    "final_capital": result["final_capital"],
                    "total_return_pct": result["total_return_pct"],
                    "mdd_pct": result["mdd_pct"]
                })

    if not results:
        print("❌ 최적화 중 오류가 발생했거나 결과가 없습니다.")
        return

    # 결과를 데이터프레임으로 변환하여 정렬
    results_df = pd.DataFrame(results)
    best_performance = results_df.sort_values(by="final_capital", ascending=False).iloc[0]
    
    print("\n\n✅ 최적화 완료!")
    print("-------------------------------------------")
    print("🏆 최고의 성과를 보인 파라미터 조합 🏆")
    print(f"단기 이동평균: {best_performance['short_window']}일")
    print(f"장기 이동평균: {best_performance['long_window']}일")
    print(f"최종 자산: {best_performance['final_capital']:,.0f}원")
    print(f"누적 수익률: {best_performance['total_return_pct']:.2f}%")
    print(f"최대 낙폭 (MDD): {best_performance['mdd_pct']:.2f}%")
    print("-------------------------------------------")
    
    return best_performance

if __name__ == '__main__':
    optimize_strategy()
