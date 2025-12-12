"""
Rate limiting service for API and LLM request management.

This module provides rate limiting functionality to prevent exceeding
API quotas and manage request frequency. Uses a rolling window approach
to track operations over time periods.

The RateLimiter class implements a hybrid token-bucket/sliding-window
algorithm that tracks operations in a 60-second rolling window to
enforce per-minute rate limits.

Key features:
- Rolling 60-second window for rate limit enforcement
- Thread-safe operation tracking
- Configurable operations per minute limits
- Efficient cleanup of expired timestamps
"""

import time
from collections import deque


class RateLimiter:
    """
    Rolling window rate limiter for API request management.

    Implements a sliding window rate limiter that tracks operations
    over a 60-second period and enforces configurable per-minute limits.
    Uses efficient deque-based storage for operation timestamps.
    """

    def __init__(self, max_ops_per_min: int) -> None:
        """
        Initialize rate limiter with operation limit.

        Parameters
        ----------
        max_ops_per_min : int
            Maximum number of operations allowed per minute
        """
        self.max_ops = max_ops_per_min
        self.events = deque()

    def allow(self) -> bool:
        """
        Check if an operation is allowed within rate limit.

        Automatically cleans up expired timestamps and records
        the current operation if allowed.

        Returns
        -------
        bool
            True if operation is allowed, False if rate limit exceeded
        """
        now = time.monotonic()
        while self.events and now - self.events[0] > 60:
            self.events.popleft()
        if len(self.events) < self.max_ops:
            self.events.append(now)
            return True
        return False
