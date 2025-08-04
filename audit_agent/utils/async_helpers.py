"""
Async utilities for handling event loops safely
"""

import asyncio
from typing import Coroutine, TypeVar, Any

T = TypeVar('T')


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    Run an async function safely, handling existing event loops
    This is useful for environments like Jupyter/Streamlit that may have active loops
    """
    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If there's a running loop, create a task
            import concurrent.futures
            import threading
            
            # Run in a thread pool to avoid blocking
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            # No running loop, we can use asyncio.run
            return asyncio.run(coro)
    except RuntimeError:
        # No event loop, create one
        return asyncio.run(coro)


async def run_with_cleanup(coro: Coroutine[Any, Any, T], cleanup_func: Coroutine = None) -> T:
    """
    Run a coroutine and ensure cleanup is called even if an error occurs
    """
    try:
        return await coro
    finally:
        if cleanup_func:
            try:
                await cleanup_func
            except Exception as e:
                print(f"Error during cleanup: {e}")