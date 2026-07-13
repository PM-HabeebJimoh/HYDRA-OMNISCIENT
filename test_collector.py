import asyncio
from core.collector import S3CausalCollector

async def test_collector():
    async with S3CausalCollector() as collector:
        print("Fetching all signals...")
        results = await collector.collect_all_parallel()
        print(f"Results: {results}")

if __name__ == "__main__":
    asyncio.run(test_collector())
