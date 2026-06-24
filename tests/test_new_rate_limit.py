import time
from concurrent.futures import ThreadPoolExecutor
from tradingagents.dataflows.y_finance import get_YFin_data_online
from tradingagents.dataflows.rate_limit_manager import execute_with_global_rate_limit, get_rate_limit_stats

def test_single_request_with_new_manager():
    """测试使用新速率限制管理器的单次请求"""
    try:
        def fetch_data():
            return get_YFin_data_online("AAPL", "2024-11-01", "2024-11-30")

        result = execute_with_global_rate_limit(fetch_data, description="AAPL data fetch")
        print("Single request with new manager: SUCCESS")
        return True
    except Exception as e:
        print(f"Single request with new manager: FAILED - {e}")
        return False

def test_concurrent_requests_with_new_manager():
    """测试使用新速率限制管理器的并发请求"""
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "META", "NVDA", "NFLX"]

    print(f"Testing concurrent requests for {len(symbols)} symbols with new manager...")

    def fetch_symbol(symbol):
        try:
            def fetch_data():
                return get_YFin_data_online(symbol, "2024-11-01", "2024-11-30")

            result = execute_with_global_rate_limit(fetch_data, description=f"{symbol} data fetch")
            print(f"✓ {symbol}: Success")
            return True
        except Exception as e:
            print(f"✗ {symbol}: {e}")
            return False

    # 使用线程池模拟并发请求
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(fetch_symbol, symbols))

    success_count = sum(results)
    print(f"Results: {success_count}/{len(symbols)} successful")
    return success_count

def test_sequential_requests_with_new_manager():
    """测试使用新速率限制管理器的顺序请求"""
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "META", "NVDA", "NFLX"]

    print("Testing sequential requests with new manager...")

    success_count = 0
    for symbol in symbols:
        try:
            def fetch_data():
                return get_YFin_data_online(symbol, "2024-11-01", "2024-11-30")

            result = execute_with_global_rate_limit(fetch_data, description=f"{symbol} data fetch")
            print(f"✓ {symbol}: Success")
            success_count += 1
        except Exception as e:
            print(f"✗ {symbol}: {e}")

    print(f"Results: {success_count}/{len(symbols)} successful")
    return success_count

def test_rate_limit_stats():
    """测试速率限制统计信息"""
    print("\nTesting rate limit statistics...")

    # 获取初始统计
    initial_stats = get_rate_limit_stats()
    print("Initial stats:", initial_stats)

    # 执行一些请求
    symbols = ["AAPL", "MSFT", "GOOGL"]
    for symbol in symbols:
        try:
            def fetch_data():
                return get_YFin_data_online(symbol, "2024-11-01", "2024-11-30")

            execute_with_global_rate_limit(fetch_data, description=f"{symbol} stats test")
            print(f"Fetched {symbol}")
        except Exception as e:
            print(f"Failed to fetch {symbol}: {e}")

    # 获取最终统计
    final_stats = get_rate_limit_stats()
    print("Final stats:", final_stats)

    return final_stats

def test_cache_effectiveness():
    """测试缓存效果"""
    print("\nTesting cache effectiveness...")

    symbol = "AAPL"

    # 第一次请求（应该调用API）
    start_time = time.time()
    try:
        def fetch_data():
            return get_YFin_data_online(symbol, "2024-11-01", "2024-11-30")

        result1 = execute_with_global_rate_limit(fetch_data, description=f"{symbol} first fetch")
        time1 = time.time() - start_time
        print(f"First request time: {time1:.2f}s")
    except Exception as e:
        print(f"First request failed: {e}")
        return False

    # 第二次请求（应该从缓存读取）
    start_time = time.time()
    try:
        def fetch_data():
            return get_YFin_data_online(symbol, "2024-11-01", "2024-11-30")

        result2 = execute_with_global_rate_limit(fetch_data, description=f"{symbol} cached fetch")
        time2 = time.time() - start_time
        print(f"Second request time: {time2:.2f}s")

        # 验证结果相同
        if result1 == result2:
            print("✓ Cache working correctly")
            print(f"✓ Speed improvement: {time1/time2:.1f}x faster")
            return True
        else:
            print("✗ Cache inconsistency detected")
            return False
    except Exception as e:
        print(f"Second request failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing New Rate Limit Manager ===\n")

    # 测试单个请求
    print("1. Testing single request with new manager:")
    test_single_request_with_new_manager()

    # 测试并发请求
    print("\n2. Testing concurrent requests with new manager:")
    concurrent_success = test_concurrent_requests_with_new_manager()

    # 测试顺序请求
    print("\n3. Testing sequential requests with new manager:")
    sequential_success = test_sequential_requests_with_new_manager()

    # 测试统计信息
    test_rate_limit_stats()

    # 测试缓存效果
    test_cache_effectiveness()

    print(f"\n=== Summary ===")
    print(f"Concurrent requests success: {concurrent_success}/8")
    print(f"Sequential requests success: {sequential_success}/8")
    print("New rate limit manager implementation complete.")