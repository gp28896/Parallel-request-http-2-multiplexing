# Cell 2 — Imports and helper functions
import asyncio
import httpx
import time
from typing import List, Tuple
from rich.console import Console

console = Console()

async def fetch(client: httpx.AsyncClient, url: str, idx: int) -> Tuple[int, str, float]:
    """
    Send GET request and return (index, url, elapsed_seconds).
    """
    start = time.perf_counter()
    try:
        resp = await client.get(url, timeout=30.0)
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
    """
    limits = httpx.Limits(max_keepalive_connections=concurrency, max_connections=concurrency)
    # Use a single AsyncClient with http2=True to enable multiplexing.
    async with httpx.AsyncClient(http2=True, limits=limits, timeout=60.0) as client:
        # Create coroutines for all requests
        tasks = [fetch(client, url, i) for i, url in enumerate(urls, start=1)]
        # Gather results concurrently
        results = await asyncio.gather(*tasks)
    return results


# Cell 4 — Example usage against an HTTP/2-capable endpoint
# Replace or extend the url list. Many public endpoints support HTTP/2 (e.g., https://nghttp2.org/httpbin/).
urls = [
    "https://nghttp2.org/httpbin/get",
    "https://www.google.com/robots.txt",
    "https://http2.golang.org/reqinfo",
    "https://httpbin.org/bytes/1024",
] * 8  # replicate to increase number of parallel requests

async def main_demo():
    console.print("[bold]Starting HTTP/2 multiplexing demo[/bold]")
    start = time.perf_counter()
    results = await run_parallel(urls, concurrency=32)
    total = time.perf_counter() - start

    # Sort results by index for readability
    results.sort(key=lambda r: r[0])
    for idx, status_url, elapsed in results:
        console.print(f"[green]{idx:03d}[/green] {status_url} — {elapsed:.3f}s")
    console.print(f"\n[bold]All done in {total:.3f}s ({len(results)} requests)[/bold]")

# Run the demo (in a Jupyter cell use: asyncio.run(main_demo()))
# In notebook, do:
await main_demo()


# Example snippet to return HTTP version
async def fetch_with_version(client: httpx.AsyncClient, url: str, idx: int):
    start = time.perf_counter()
    try:
        resp = await client.get(url)
        elapsed = time.perf_counter() - start
        return idx, resp.status_code, resp.http_version, elapsed
    except Exception as e:
        elapsed = time.perf_counter() - start
        return idx, f"ERROR {e}", None, elapsed
