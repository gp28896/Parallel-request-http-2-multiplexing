# Cell 2 — Imports and helper functions
import asyncio
import httpx
import time
from typing import List, Tuple
from rich.console import Console

console = Console()

async def fetch(client: httpx.AsyncClient, url: str, idx: int) -> Tuple[int, str, float]:
    """
    single asynchronous HTTP GET using a shared httpx.AsyncClient 
    and return (index, url, elapsed_seconds) tuple.

    Non-raising: The function converts exceptions into return values instead of propagating them. 
    This simplifies batch processing (e.g., asyncio.gather) because 
    callers can handle per-request failures without wrapping every task.

    Timing includes DNS lookup, TLS handshake, request send, 
    server processing, and response read (i.e., total wall-clock time for the get call).

    Uses the provided AsyncClient for connection reuse (important for HTTP/2 multiplexing and keep-alive).

    Timeout is per-request; adjust as needed or pass client-level default timeouts.

    The status string is compact but not structured; 
    if callers need structured data, return resp.status_code, 
    resp.http_version, resp.headers, or resp.text/json instead.

    Exception stringification uses the exception's str which may be 
    sufficient for logs but not for programmatic error handling.
    """
    start = time.perf_counter()
    try:
        # await suspends this coroutine until the request completes
        resp = await client.get(url, timeout=30.0) # Asynchronous
        elapsed = time.perf_counter() - start
        return idx, f"{resp.status_code} {url}", elapsed
    except Exception as e:
        elapsed = time.perf_counter() - start
        return idx, f"ERROR {e} {url}", elapsed

# Cell 3 — Main concurrency demonstration
async def run_parallel(urls: List[str], concurrency: int = 16) -> List[Tuple[int, str, float]]:
    """
    Create a single HTTP/2 connection (AsyncClient with http2=True) and
    dispatch many requests concurrently using asyncio.gather.
    returning a list of per-request result tuples.
    """
    limits = httpx.Limits(max_keepalive_connections=concurrency, max_connections=concurrency)
    # Use a single AsyncClient with http2=True to enable multiplexing.
    # http2=True: enables HTTP/2 support so requests to the same origin can be multiplexed over one connection.
    # Using a single client enables connection reuse 
    # (TCP/TLS and HTTP/2 streams) and efficient resource management
    async with httpx.AsyncClient(http2=True, limits=limits, timeout=60.0) as client:
        # Create coroutines for all requests
        # Constructs a list of coroutines (not yet running) 
        # by calling the fetch coroutine factory for each URL with a numeric index
        tasks = [fetch(client, url, i) for i, url in enumerate(urls, start=1)]
        # Gather results concurrently
        # Schedules all coroutines concurrently and waits for them to complete
        # asyncio.gather runs all tasks concurrently on the event loop; 
        # exceptions in individual tasks propagate by default 
        # (but fetch returns exceptions as values, so gather will usually succeed).
        # Because a single client with http2=True is used, 
        # many of these concurrent operations will be multiplexed 
        # over the same HTTP/2 connection for the same origin.
        results = await asyncio.gather(*tasks)
        # Returns the list of tuples produced by fetch, 
        # preserving the order of the tasks as created (which matches enumeration order).
    return results


# Cell 4 — Example usage against an HTTP/2-capable endpoint
# Replace or extend the url list. 
# Many public endpoints support HTTP/2 (e.g., https://nghttp2.org/httpbin/).
urls = [
    "https://nghttp2.org/httpbin/get",
    "https://www.google.com/robots.txt",
    "https://http2.golang.org/reqinfo",
    "https://httpbin.org/bytes/1024",
] * 8  # replicate to increase number of parallel requests

async def main_demo():
    # Example driver that measures total runtime, 
    # invokes run_parallel with a sample URL list, 
    # sorts and prints results, and shows aggregate timing*
    console.print("[bold]Starting HTTP/2 multiplexing demo[/bold]")
    start = time.perf_counter()
    # Calls run_parallel with the predefined urls list 
    # and a concurrency limit of 32 (configures client limits).
    # Awaits completion and stores the returned list of (idx, status_url, elapsed) tuples
    results = await run_parallel(urls, concurrency=32)
    total = time.perf_counter() - start

    # Sort results by index for readability
    # Sorts results in-place by the request index so output 
    # is in numeric order (useful when gather returns results 
    # in the creation order, but sorting guarantees readability if indices are non-monotonic).
    results.sort(key=lambda r: r[0])
    # prints each entry with formatted index, status string, and per-request elapsed time.
    for idx, status_url, elapsed in results:
        console.print(f"[green]{idx:03d}[/green] {status_url} — {elapsed:.3f}s")
    console.print(f"\n[bold]All done in {total:.3f}s ({len(results)} requests)[/bold]")

# Run the demo (in a Jupyter cell use: asyncio.run(main_demo()))
# In notebook, do:
# await main_demo()


# Example snippet to return HTTP version
# Variant of fetch that returns structured information including HTTP version used by the response.
# Sends an asynchronous GET request using the provided client.
async def fetch_with_version(client: httpx.AsyncClient, url: str, idx: int):
    start = time.perf_counter()
    try:
        # On success computes elapsed time and returns a tuple:
        #     idx: request identifier
        #     resp.status_code: integer HTTP status code (e.g., 200)
        #     resp.http_version: string indicating protocol version (e.g., "HTTP/2")
        #     elapsed: float seconds for the request
        resp = await client.get(url)
        elapsed = time.perf_counter() - start
        return idx, resp.status_code, resp.http_version, elapsed
    except Exception as e:
        elapsed = time.perf_counter() - start
        return idx, f"ERROR {e}", None, elapsed
