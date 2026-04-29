"""
Utility for running blocking (synchronous) code from async FastAPI endpoints
without blocking the event loop.

Usage:
    result = await run_sync(some_blocking_function, arg1, arg2)
    result = await run_sync(lambda: db.query(Model).filter(...).first())
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any, Callable, TypeVar

T = TypeVar("T")

# Shared executor — sized to match the DB connection pool (default 10 workers)
_executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="hedera-sync")


async def run_sync(fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """
    Run a blocking callable in the shared thread pool and await the result.

    Args:
        fn:     Any blocking callable (SQLAlchemy query, requests.get, time.sleep, etc.)
        *args:  Positional arguments forwarded to fn
        **kwargs: Keyword arguments forwarded to fn

    Returns:
        Whatever fn returns.

    Example:
        user = await run_sync(db.query(User).filter(User.id == uid).first)
        resp = await run_sync(requests.get, url, timeout=10)
    """
    loop = asyncio.get_running_loop()
    if args or kwargs:
        fn = partial(fn, *args, **kwargs)
    return await loop.run_in_executor(_executor, fn)
