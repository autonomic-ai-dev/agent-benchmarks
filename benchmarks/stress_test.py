import asyncio
import aiohttp
import time
import statistics
import argparse
import os

DAEMONS = {
    "agent-brain": 3100,
    "agent-heart": 3101,
    "agent-nerves": 3102,
    "agent-muscle": 3103,
    "agent-mouth": 3104,
    "agent-eyes": 3105,
    "agent-immune": 3106,
    "agent-spine": 3000,
}

async def fetch_health(session, url):
    start = time.perf_counter()
    try:
        async with session.get(url, timeout=10) as response:
            await response.text()
            latency = time.perf_counter() - start
            return (response.status, latency)
    except Exception as e:
        return (str(e), time.perf_counter() - start)

async def stress_test_target(session, url, concurrency, duration):
    timeout = time.time() + duration
    tasks = []
    latencies = []
    status_codes = {}
    
    while time.time() < timeout:
        while len(tasks) < concurrency:
            tasks.append(asyncio.create_task(fetch_health(session, url)))
        
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            status, latency = task.result()
            latencies.append(latency)
            status_codes[status] = status_codes.get(status, 0) + 1
        tasks = list(pending)
        
    if tasks:
        done, _ = await asyncio.wait(tasks)
        for task in done:
            status, latency = task.result()
            latencies.append(latency)
            status_codes[status] = status_codes.get(status, 0) + 1

    return latencies, status_codes

async def stress_test_all(concurrency_per_target, duration):
    print(f"Starting ecosystem stress test.")
    print(f"Concurrency per target: {concurrency_per_target}, Duration: {duration}s")
    
    async with aiohttp.ClientSession() as session:
        tasks = {}
        for daemon, port in DAEMONS.items():
            url = f"http://{daemon}:{port}/health"
            tasks[daemon] = asyncio.create_task(stress_test_target(session, url, concurrency_per_target, duration))
        
        results = await asyncio.gather(*tasks.values())
        
    os.makedirs("benchmarks", exist_ok=True)
    with open("benchmarks/results.md", "w") as f:
        f.write("# Ecosystem Benchmark Results\n\n")
        f.write(f"**Concurrency per target:** {concurrency_per_target}\n")
        f.write(f"**Duration:** {duration}s\n\n")
        
        for daemon, (latencies, status_codes) in zip(tasks.keys(), results):
            total_requests = len(latencies)
            if total_requests == 0:
                print(f"{daemon}: No requests completed.")
                continue

            req_per_sec = total_requests / duration
            avg_latency = statistics.mean(latencies) * 1000
            p95_latency = statistics.quantiles(latencies, n=100)[94] * 1000 if total_requests >= 100 else 0

            print(f"\n--- {daemon} ---")
            print(f"Throughput: {req_per_sec:.2f} req/sec | Avg Latency: {avg_latency:.2f} ms | p95 Latency: {p95_latency:.2f} ms")
            
            f.write(f"## {daemon}\n")
            f.write(f"- **Total Requests**: {total_requests}\n")
            f.write(f"- **Throughput**: {req_per_sec:.2f} req/sec\n")
            f.write(f"- **Average Latency**: {avg_latency:.2f} ms\n")
            f.write(f"- **p95 Latency**: {p95_latency:.2f} ms\n")
            f.write(f"- **Status Codes**: `{status_codes}`\n\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autonomic Benchmark Tool")
    parser.add_argument("-c", "--concurrency", type=int, default=20, help="Concurrent connections per target")
    parser.add_argument("-d", "--duration", type=int, default=10, help="Test duration in seconds")
    args = parser.parse_args()
    
    asyncio.run(stress_test_all(args.concurrency, args.duration))
