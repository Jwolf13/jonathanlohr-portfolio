"""
Retry decorator for AWS API calls.

Implements exponential backoff with jitter for handling throttling and
transient failures. Works with any function but designed for boto3 calls.

DDIA Connection (Ch. 8 — The Trouble with Distributed Systems):
    Retries with exponential backoff is a fundamental pattern for handling
    transient faults in distributed systems (like AWS APIs).
"""

import logging
import time
import random
from functools import wraps
from typing import Callable, Type, Tuple, Any

import boto3
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 5,
    base_delay: float = 0.1,
    max_delay: float = 32.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    catch_exceptions: Tuple[Type[Exception], ...] = (
        ClientError,
        BotoCoreError,
        TimeoutError,
    ),
):
    """
    Decorator for retrying functions with exponential backoff.

    Retries on specified exceptions with exponential backoff + optional jitter.
    Specifically handles botocore ThrottlingException.

    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay between retries.
        backoff_factor: Multiplicative factor for delay (default 2.0 = exponential).
        jitter: If True, add randomness to delay (recommended).
        catch_exceptions: Tuple of exception types to catch and retry on.

    Returns:
        Decorator function.

    Example:
        @retry_with_backoff(max_retries=5)
        def call_security_hub():
            return client.get_findings()
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            delay = base_delay

            while attempt <= max_retries:
                try:
                    return func(*args, **kwargs)

                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "Unknown")

                    # Always retry on throttling
                    if error_code == "ThrottlingException":
                        if attempt >= max_retries:
                            logger.error(
                                f"Max retries exceeded for {func.__name__} "
                                f"(ThrottlingException after {attempt} attempts)"
                            )
                            raise

                        logger.warning(
                            f"Throttled on {func.__name__}, retrying in {delay:.2f}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                        if jitter:
                            delay += random.uniform(0, delay * 0.1)
                        attempt += 1
                        continue

                    # For other client errors, don't retry
                    logger.error(
                        f"ClientError in {func.__name__}: {error_code} - {str(e)}"
                    )
                    raise

                except BotoCoreError as e:
                    if attempt >= max_retries:
                        logger.error(
                            f"Max retries exceeded for {func.__name__} "
                            f"(BotoCoreError after {attempt} attempts)"
                        )
                        raise

                    logger.warning(
                        f"BotoCoreError in {func.__name__}, retrying in {delay:.2f}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)
                    if jitter:
                        delay += random.uniform(0, delay * 0.1)
                    attempt += 1
                    continue

                except Exception as e:
                    # Don't retry for non-boto exceptions unless explicitly caught
                    if not isinstance(e, catch_exceptions):
                        raise

                    if attempt >= max_retries:
                        logger.error(
                            f"Max retries exceeded for {func.__name__} "
                            f"({type(e).__name__} after {attempt} attempts)"
                        )
                        raise

                    logger.warning(
                        f"Exception in {func.__name__}, retrying in {delay:.2f}s "
                        f"(attempt {attempt + 1}/{max_retries}): {str(e)}"
                    )
                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)
                    if jitter:
                        delay += random.uniform(0, delay * 0.1)
                    attempt += 1
                    continue

            # Should never reach here
            raise RuntimeError(f"Unexpected exit from retry loop in {func.__name__}")

        return wrapper

    return decorator
