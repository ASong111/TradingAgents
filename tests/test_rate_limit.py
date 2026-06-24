import time
from concurrent.futures import ThreadPoolExecutor
from tradingagents.dataflows.y_finance import get_YFin_data_online

def test_single_request():
    """测试单次请求"""
    try:
        result = get_YFin_data_online("AAPL", "2024-11-01", "2024-11-30")
        print("Single request successful")
        return True
    except Exception as e:
        print(f"Single request failed: {e}")
        return False

def test_rapid_requests():
    """测试快速连续请求"""
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "META", "NVDA", "NFLX"]

    print(f"Testing rapid requests for {len(symbols)} symbols...")

    def fetch_symbol(symbol):
        try:
            result = get_YFin_data_online(symbol, "2024-11-01", "2024-11-30")
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
    return success_count == len(symbols)

def test_with_delay():
    """测试带延迟的请求"""
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "META", "NVDA", "NFLX"]

    print("Testing requests with 1-second delay...")

    success_count = 0
    for i, symbol in enumerate(symbols):
        try:
            result = get_YFin_data_online(symbol, "2024-11-01", "2024-11-30")
            print(f"✓ {symbol}: Success")
            success_count += 1
        except Exception as e:
            print(f"✗ {symbol}: {e}")

        # 添加延迟
        if i < len(symbols) - 1:
            time.sleep(1)

    print(f"Results: {success_count}/{len(symbols)} successful")
    return success_count == len(symbols)

if __name__ == "__main__":
    print("=== Testing Yahoo Finance Rate Limits ===\n")

    print("1. Testing single request:")
    test_single_request()

    print("\n2. Testing rapid concurrent requests:")
    test_rapid_requests()

    print("\n3. Testing requests with delay:")
    test_with_delay()