"""
Yahoo Finance Rate Limit Manager
Provides centralized rate limiting and request coordination for yfinance API calls.
"""

import logging
import threading
import time
from collections import deque
from typing import Any, Callable, Optional

import yfinance as yf
from yfinance.exceptions import YFRateLimitError

logger = logging.getLogger(__name__)


class RateLimitManager:
    """Global rate limit manager for Yahoo Finance API calls."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the rate limit manager."""
        self._request_history = deque(maxlen=100)  # Track last 100 requests
        self._request_lock = threading.RLock()
        self._concurrent_requests = 0
        self._max_concurrent = 2  # Maximum concurrent yfinance requests
        self._min_interval = 0.5  # Minimum seconds between requests
        self._max_interval = 10.0  # Maximum backoff interval
        self._concurrency_semaphore = threading.Semaphore(self._max_concurrent)

    def _calculate_wait_time(self) -> float:
        """Calculate appropriate wait time based on recent request history."""
        if not self._request_history:
            return 0.0

        now = time.time()
        recent_requests = [t for t in self._request_history if now - t < 60]  # Last minute

        if len(recent_requests) < 10:
            return 0.0  # No need to wait if under 10 requests per minute

        # Calculate average interval
        if len(recent_requests) > 1:
            intervals = [recent_requests[i+1] - recent_requests[i]
                        for i in range(len(recent_requests)-1)]
            avg_interval = sum(intervals) / len(intervals)
        else:
            avg_interval = 1.0

        # Adjust wait time based on recent frequency
        target_interval = max(self._min_interval, min(self._max_interval, avg_interval * 1.5))
        last_request = self._request_history[-1]
        elapsed = now - last_request

        return max(0.0, target_interval - elapsed)

    def _record_request(self):
        """Record a successful API request."""
        with self._request_lock:
            self._request_history.append(time.time())

    def execute_with_rate_limit(self, func: Callable[[], Any],
                               max_retries: int = 3,
                               description: str = "yfinance request") -> Any:
        """
        Execute a yfinance function with rate limiting and retry logic.

        Args:
            func: Function to execute
            max_retries: Maximum number of retry attempts
            description: Description for logging

        Returns:
            Function result

        Raises:
            YFRateLimitError: If all retries fail due to rate limiting
            Exception: For other types of errors
        """
        # Wait for concurrency slot
        with self._concurrency_semaphore:
            # Calculate and apply initial wait
            wait_time = self._calculate_wait_time()
            if wait_time > 0:
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s before {description}")
                time.sleep(wait_time)

            for attempt in range(max_retries + 1):
                try:
                    result = func()
                    self._record_request()
                    return result
                except YFRateLimitError:
                    if attempt < max_retries:
                        # Exponential backoff with jitter
                        delay = min(self._max_interval,
                                  self._min_interval * (2 ** attempt))
                        jitter = delay * 0.1  # 10% jitter
                        delay_with_jitter = delay + (jitter * (2 * (time.time() % 1) - 1))

                        logger.warning(
                            f"Yahoo Finance rate limited on {description}, "
                            f"retrying in {delay_with_jitter:.1f}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(delay_with_jitter)
                    else:
                        logger.error(f"Yahoo Finance rate limit exceeded for {description}")
                        raise
                except Exception as e:
                    # For non-rate-limit errors, don't retry
                    if attempt == 0:
                        logger.error(f"Error executing {description}: {e}")
                    raise

    def get_stats(self) -> dict:
        """Get current rate limiting statistics."""
        with self._request_lock:
            now = time.time()
            recent_requests = [t for t in self._request_history if now - t < 300]  # Last 5 minutes

            return {
                "total_requests": len(self._request_history),
                "recent_requests_5min": len(recent_requests),
                "concurrent_requests": self._concurrent_requests,
                "max_concurrent": self._max_concurrent,
            }


# Global instance
_rate_limit_manager = RateLimitManager()


def execute_with_global_rate_limit(func: Callable[[], Any],
                                  max_retries: int = 3,
                                  description: str = "yfinance request") -> Any:
    """
    Convenience function to execute with global rate limiting.

    This should be used instead of the local yf_retry function for all
    yfinance API calls to ensure proper rate limit coordination.
    """
    return _rate_limit_manager.execute_with_rate_limit(func, max_retries, description)


def get_rate_limit_stats() -> dict:
    """Get current rate limiting statistics."""
    return _rate_limit_manager.get_stats()