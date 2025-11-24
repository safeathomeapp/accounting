"""
Retry logic for failed sync operations.

Implements exponential backoff for retrying failed syncs with
configurable max attempts and delay calculations.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class RetryManager:
    """
    Manages retry logic for failed sync operations.

    Uses exponential backoff: delay = base_delay * (2 ^ attempt)
    """

    def __init__(self, max_retries: int = 3, base_delay: int = 60):
        """
        Initialize retry manager.

        Args:
            max_retries: Maximum number of retry attempts (default 3)
            base_delay: Base delay in seconds (default 60)
        """
        self.max_retries = max_retries
        self.base_delay = base_delay

    def calculate_backoff(self, attempt: int) -> int:
        """
        Calculate delay for exponential backoff.

        Formula: base_delay * (2 ^ attempt)
        Examples (base_delay=60):
            - attempt 0: 60 seconds
            - attempt 1: 120 seconds
            - attempt 2: 240 seconds
            - attempt 3: 480 seconds (8 minutes)

        Args:
            attempt: Retry attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        if attempt < 0:
            return self.base_delay

        return self.base_delay * (2 ** attempt)

    def calculate_next_retry_time(self, attempt: int) -> datetime:
        """
        Calculate when next retry should happen.

        Args:
            attempt: Current retry attempt number

        Returns:
            Datetime for next retry
        """
        delay_seconds = self.calculate_backoff(attempt)
        return datetime.utcnow() + timedelta(seconds=delay_seconds)

    def should_retry(self, retry_count: int) -> bool:
        """
        Determine if sync should be retried.

        Args:
            retry_count: Current number of retries performed

        Returns:
            True if should retry, False if max retries exceeded
        """
        if retry_count >= self.max_retries:
            logger.warning(f"Max retries ({self.max_retries}) exceeded")
            return False

        return True

    def get_retry_info(self, retry_count: int) -> Optional[dict]:
        """
        Get retry information for a failed sync.

        Returns info about whether and when to retry.

        Args:
            retry_count: Current number of retries

        Returns:
            Dict with {'should_retry': bool, 'next_retry_at': datetime, 'delay_seconds': int}
            None if should not retry
        """
        if not self.should_retry(retry_count):
            return None

        delay_seconds = self.calculate_backoff(retry_count)
        next_retry_at = self.calculate_next_retry_time(retry_count)

        return {
            "should_retry": True,
            "next_retry_at": next_retry_at,
            "delay_seconds": delay_seconds,
            "attempt_number": retry_count + 1,
            "max_attempts": self.max_retries
        }

    def format_retry_message(self, retry_count: int) -> str:
        """
        Format a human-readable retry message.

        Args:
            retry_count: Current number of retries

        Returns:
            Formatted message about retry status
        """
        if not self.should_retry(retry_count):
            return f"Max retries ({self.max_retries}) exceeded, giving up"

        delay_seconds = self.calculate_backoff(retry_count)
        next_retry_at = self.calculate_next_retry_time(retry_count)

        # Format delay nicely
        if delay_seconds < 60:
            delay_str = f"{delay_seconds} seconds"
        elif delay_seconds < 3600:
            minutes = delay_seconds / 60
            delay_str = f"{minutes:.1f} minutes"
        else:
            hours = delay_seconds / 3600
            delay_str = f"{hours:.1f} hours"

        return (
            f"Retry {retry_count + 1}/{self.max_retries} scheduled for "
            f"{next_retry_at.isoformat()} ({delay_str} delay)"
        )
