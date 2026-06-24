import time
import logging
from tradingagents.dataflows.rate_limit_manager import execute_with_global_rate_limit, get_rate_limit_stats
from tradingagents.dataflows.y_finance import get_YFin_data_online

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_very_gentle_requests():
    """非常温和的测试，避免触发速率限制"""
    symbols = ["AAPL", "MSFT"]  # 只测试两个符号

    print("Testing very gentle requests with 5-second delays...")

    success_count = 0
    for i, symbol in enumerate(symbols):
        try:
            def fetch_data():
                return get_YFin_data_online(symbol, "2024-11-01", "2024-11-05")  # 短时间范围

            result = execute_with_global_rate_limit(
                fetch_data,
                max_retries=5,  # 更多重试次数
                description=f"{symbol} gentle fetch"
            )
            print(f"✓ {symbol}: Success")
            success_count += 1

            # 在请求之间添加长延迟
            if i < len(symbols) - 1:
                print("Waiting 10 seconds before next request...")
                time.sleep(10)

        except Exception as e:
            print(f"✗ {symbol}: {e}")

    print(f"Results: {success_count}/{len(symbols)} successful")
    return success_count

def test_single_symbol_multiple_days():
    """测试单个符号的多天数据获取"""
    symbol = "AAPL"
    print(f"\nTesting {symbol} with multiple date ranges...")

    date_ranges = [
        ("2024-11-01", "2024-11-05"),
        ("2024-11-06", "2024-11-10"),
        ("2024-11-11", "2024-11-15"),
    ]

    success_count = 0
    for start_date, end_date in date_ranges:
        try:
            def fetch_data():
                return get_YFin_data_online(symbol, start_date, end_date)

            result = execute_with_global_rate_limit(
                fetch_data,
                max_retries=3,
                description=f"{symbol} {start_date} to {end_date}"
            )
            print(f"✓ {symbol} {start_date}-{end_date}: Success")
            success_count += 1

            # 在每次请求后等待
            if start_date != date_ranges[-1][0]:
                print("Waiting 15 seconds before next request...")
                time.sleep(15)

        except Exception as e:
            print(f"✗ {symbol} {start_date}-{end_date}: {e}")

    print(f"Results: {success_count}/{len(date_ranges)} successful")
    return success_count

def test_cache_only():
    """测试仅使用缓存的数据"""
    print("\nTesting cache-only operations...")

    # 首先获取一些数据到缓存
    symbol = "AAPL"
    try:
        def fetch_initial():
            return get_YFin_data_online(symbol, "2024-11-01", "2024-11-05")

        result1 = execute_with_global_rate_limit(fetch_initial, description="Initial cache load")
        print("✓ Initial data cached")

        # 立即再次请求相同数据（应该从缓存读取）
        def fetch_cached():
            return get_YFin_data_online(symbol, "2024-11-01", "2024-11-05")

        result2 = execute_with_global_rate_limit(fetch_cached, description="Cached data fetch")
        print("✓ Cached data retrieved")

        if result1 == result2:
            print("✓ Cache consistency verified")
            return True
        else:
            print("✗ Cache inconsistency detected")
            return False

    except Exception as e:
        print(f"✗ Cache test failed: {e}")
        return False

def main():
    print("=== Gentle Rate Limit Testing ===\n")

    # 先等待一段时间确保速率限制重置
    print("Waiting 30 seconds to ensure rate limit reset...")
    time.sleep(30)

    # 测试1: 温和请求
    print("\n1. Testing very gentle requests:")
    gentle_success = test_very_gentle_requests()

    # 等待一段时间
    print("\nWaiting 30 seconds before next test...")
    time.sleep(30)

    # 测试2: 单个符号多天数据
    print("\n2. Testing single symbol with multiple date ranges:")
    single_symbol_success = test_single_symbol_multiple_days()

    # 测试3: 缓存测试
    print("\n3. Testing cache operations:")
    cache_success = test_cache_only()

    # 显示统计信息
    stats = get_rate_limit_stats()
    print(f"\n=== Final Statistics ===")
    print(f"Total requests: {stats['total_requests']}")
    print(f"Recent requests (5min): {stats['recent_requests_5min']}")
    print(f"Gentle requests success: {gentle_success}/2")
    print(f"Single symbol success: {single_symbol_success}/3")
    print(f"Cache test: {'PASS' if cache_success else 'FAIL'}")

if __name__ == "__main__":
    main()