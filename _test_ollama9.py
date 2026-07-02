import asyncio, httpx

async def test():
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Try with reduced context
        r = await client.post("http://localhost:11434/api/generate", json={
            "model": "deepseek-coder",
            "prompt": "Hello",
            "stream": False,
            "options": {"num_ctx": 2048, "num_gpu": 1}
        })
        print(f"Status: {r.status_code}")
        print(f"Body: {r.text[:1000]}")

asyncio.run(test())
