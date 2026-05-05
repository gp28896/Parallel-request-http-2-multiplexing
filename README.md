# Parallel-request-http-2-multiplexing
A Jupyter Notebook that demonstrates sending multiple HTTP/2 requests in parallel using a single multiplexed connection with httpx and asyncio.
HTTP/2 Multiplexing Demo — Jupyter Notebook

Multiplexing (networking context) is the ability to carry multiple independent logical streams of data concurrently over a single underlying transport connection. Key points:

    What it does: lets many requests/responses share one TCP/TLS connection so they can be sent and received interleaved without waiting for each other to finish.
    Why it matters: reduces connection overhead (fewer TCP/TLS handshakes), improves latency for many small requests, and increases throughput by better utilizing a single connection.
    How it works (HTTP/2 example):
        A connection is split into independent streams, each with a unique stream identifier.
        Frames (units of data/control) for different streams are interleaved on the wire and carry stream IDs so endpoints can demultiplex them.
        Flow control and prioritization let endpoints limit and order resource use per stream.
    Benefits:
        Lower connection setup cost, fewer sockets, better reuse of TLS session.
        Eliminates head-of-line blocking at the HTTP request layer (requests don’t need to wait for prior responses) — though TCP-level head-of-line
        blocking still exists.
        Enables server push and request prioritization.
    Trade-offs & considerations:
        Complexity: protocol and implementation complexity increases (stream management, flow control, prioritization).
        TCP-level head-of-line blocking still applies; QUIC (used by HTTP/3) avoids that by operating over UDP with independent packet streams.
        Multiplexing is per-origin/connection — requests to different hosts require separate connections.
    When to use: workloads with many small, concurrent requests to the same origin (e.g., web assets, API fan-out) benefit most.

A concise Jupyter Notebook that demonstrates sending multiple HTTP/2 requests in parallel using a single multiplexed connection with httpx and asyncio.
Features

    Uses a single httpx.AsyncClient with http2=True to enable HTTP/2 multiplexing.
    Dispatches many concurrent requests over the same origin to show connection reuse and reduced latency.
    Simple helper to measure request durations and report HTTP version per response (optional).
    Works with Python 3.8+.

Requirements

    Python 3.8+
    Packages:
        httpx (with http2 support)
        rich (optional, for nicer console output)

Install:
bash

pip install "httpx[http2]" rich

Notebook Cells Overview

    Cell 1 — Setup / Install
        Optional pip install command for dependencies.
    Cell 2 — Imports and helper functions
        Imports asyncio, httpx, time, typing, and rich.
        fetch(client, url, idx) — coroutine that GETs a URL, returns index, status/info, and elapsed seconds.
    Cell 3 — Main concurrency demonstration
        run_parallel(urls, concurrency=16) — creates a single AsyncClient(http2=True) and dispatches all requests via asyncio.gather.
        Uses httpx.Limits to control connection limits.
    Cell 4 — Example usage
        Example list of HTTP/2-capable endpoints (replace as needed).
        main_demo() runs the demo, prints per-request timings, and total run time.
        In a notebook cell run: await main_demo()
    Cell 5 — Notes and troubleshooting
        Points about server HTTP/2 support, per-origin multiplexing, and tuning.

Usage

    Open the notebook in Jupyter or JupyterLab.
    Install dependencies if needed (Cell 1).
    Adjust the urls list in Cell 4 to target endpoints you control or know support HTTP/2.
    Run each cell in order. In the final cell use:

python

await main_demo()

(or asyncio.run(main_demo()) if running outside an interactive notebook).
Example: Inspect HTTP version

To verify whether responses used HTTP/2, replace fetch with fetch_with_version that returns resp.http_version and print it in the results.

Example snippet:
python

async def fetch_with_version(client: httpx.AsyncClient, url: str, idx: int):
    start = time.perf_counter()
    try:
        resp = await client.get(url, timeout=30.0)
        elapsed = time.perf_counter() - start
        return idx, resp.status_code, resp.http_version, elapsed
    except Exception as e:
        elapsed = time.perf_counter() - start
        return idx, f"ERROR {e}", None, time.perf_counter() - start

Tips

    Multiplexing is per-origin: group many requests against the same host to see benefits.
    If a server doesn't support HTTP/2, httpx will fall back to HTTP/1.1; check resp.http_version.
    Tune httpx.Limits and the number of concurrent tasks for higher throughput or to avoid overwhelming servers.

License

MIT License — use and modify freely.
