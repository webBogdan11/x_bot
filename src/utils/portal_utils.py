from __future__ import annotations

import asyncio
import logging
import random
from functools import wraps
from typing import Awaitable, Callable, Type

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page, TimeoutError


logger = logging.getLogger(__name__)


async def human_type(
    page: Page, selector: str, text: str, min_delay: int = 50, max_delay: int = 150
) -> None:
    """
    Simulate human typing on a page.

    Parameters
    ----------
    page : Page
        The page to type on.
    selector : str
    """
    for ch in text:
        await page.type(selector, ch, delay=random.randint(min_delay, max_delay))


def async_retry(
    *,
    retries: int = 3,
    backoff: float = 1.5,
    exc: tuple[Type[BaseException], ...] = (TimeoutError, PlaywrightError),
) -> Callable[[Callable[..., Awaitable]], Callable[..., Awaitable]]:
    """
    Decorator that retries an *async* function when it raises *exc*.

    Parameters
    ----------
    retries : int
        Maximum number of additional attempts.
    backoff : float
        Multiplier for exponential back-off (first delay == backoff seconds).
    exc : tuple[type[BaseException], …]
        Exception classes that trigger a retry.
    """

    def decorator(fn: Callable[..., Awaitable]):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            delay = backoff
            for attempt in range(retries + 1):  # initial try + N retries
                try:
                    return await fn(*args, **kwargs)
                except exc as e:
                    if attempt == retries:
                        logger.exception(
                            "Retries exhausted for %s after %s attempts",
                            fn.__qualname__,
                            attempt + 1,
                        )
                        raise
                    log = getattr(args[0], "logger", logger)  # fall back to module log
                    log.warning(
                        "%s failed (%s). Retrying %s/%s in %.1fs…",
                        fn.__qualname__,
                        e.__class__.__name__,
                        attempt + 1,
                        retries,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    delay *= backoff

        return wrapper

    return decorator
