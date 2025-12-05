"""
Rate Limiter - Prevents overwhelming Common Crawl servers
"""

import time
import threading
from typing import Optional
from collections import deque


class RateLimiter:
    """Token bucket rate limiter for API requests"""

    def __init__(self, requests_per_second: float = 2.0, burst: int = 5):
        """
        Initialize rate limiter

        Args:
            requests_per_second: Maximum sustained request rate
            burst: Maximum burst size (tokens in bucket)
        """
        self.rate = requests_per_second
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()
        self.lock = threading.Lock()

    def acquire(self, tokens: int = 1, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Acquire tokens from the bucket

        Args:
            tokens: Number of tokens to acquire
            blocking: If True, wait for tokens to become available
            timeout: Maximum time to wait (None = wait forever)

        Returns:
            True if tokens were acquired, False otherwise
        """
        start_time = time.time()

        while True:
            with self.lock:
                # Refill bucket based on elapsed time
                now = time.time()
                elapsed = now - self.last_update
                self.tokens = min(
                    self.burst,
                    self.tokens + elapsed * self.rate
                )
                self.last_update = now

                # Try to acquire tokens
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

            if not blocking:
                return False

            if timeout is not None and (time.time() - start_time) >= timeout:
                return False

            # Calculate sleep time
            with self.lock:
                tokens_needed = tokens - self.tokens
                sleep_time = tokens_needed / self.rate

            time.sleep(min(sleep_time, 0.1))  # Sleep in small increments

    def __enter__(self):
        """Context manager entry"""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        pass


class SlidingWindowRateLimiter:
    """Sliding window rate limiter - more accurate but higher memory"""

    def __init__(self, requests_per_second: float = 2.0, window_size: float = 1.0):
        """
        Initialize sliding window rate limiter

        Args:
            requests_per_second: Maximum request rate
            window_size: Time window in seconds
        """
        self.rate = requests_per_second
        self.window_size = window_size
        self.max_requests = int(requests_per_second * window_size)
        self.requests = deque()
        self.lock = threading.Lock()

    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Acquire permission to make a request

        Args:
            blocking: If True, wait until request can be made
            timeout: Maximum time to wait

        Returns:
            True if request can be made, False otherwise
        """
        start_time = time.time()

        while True:
            with self.lock:
                now = time.time()

                # Remove old requests outside window
                while self.requests and self.requests[0] < now - self.window_size:
                    self.requests.popleft()

                # Check if we can make request
                if len(self.requests) < self.max_requests:
                    self.requests.append(now)
                    return True

            if not blocking:
                return False

            if timeout is not None and (time.time() - start_time) >= timeout:
                return False

            # Calculate sleep time
            with self.lock:
                if self.requests:
                    oldest = self.requests[0]
                    sleep_time = (oldest + self.window_size) - time.time()
                    time.sleep(max(0, sleep_time))
                else:
                    time.sleep(0.1)

    def __enter__(self):
        """Context manager entry"""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        pass


class AdaptiveRateLimiter:
    """Rate limiter that adapts based on errors"""

    def __init__(
        self,
        initial_rate: float = 2.0,
        min_rate: float = 0.5,
        max_rate: float = 10.0,
        increase_factor: float = 1.2,
        decrease_factor: float = 0.5
    ):
        """
        Initialize adaptive rate limiter

        Args:
            initial_rate: Starting request rate
            min_rate: Minimum allowed rate
            max_rate: Maximum allowed rate
            increase_factor: Multiply rate by this on success
            decrease_factor: Multiply rate by this on error
        """
        self.current_rate = initial_rate
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.increase_factor = increase_factor
        self.decrease_factor = decrease_factor
        self.limiter = RateLimiter(requests_per_second=initial_rate)
        self.lock = threading.Lock()
        self.success_count = 0
        self.error_count = 0

    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        """Acquire permission to make request"""
        return self.limiter.acquire(blocking=blocking, timeout=timeout)

    def report_success(self):
        """Report successful request - may increase rate"""
        with self.lock:
            self.success_count += 1

            # Increase rate after every 10 successful requests
            if self.success_count >= 10:
                self.success_count = 0
                new_rate = min(self.max_rate, self.current_rate * self.increase_factor)
                if new_rate != self.current_rate:
                    self.current_rate = new_rate
                    self.limiter = RateLimiter(requests_per_second=new_rate)

    def report_error(self):
        """Report failed request - will decrease rate"""
        with self.lock:
            self.error_count += 1
            self.success_count = 0  # Reset success count

            # Decrease rate immediately on error
            new_rate = max(self.min_rate, self.current_rate * self.decrease_factor)
            if new_rate != self.current_rate:
                self.current_rate = new_rate
                self.limiter = RateLimiter(requests_per_second=new_rate)

    def get_current_rate(self) -> float:
        """Get current request rate"""
        with self.lock:
            return self.current_rate
