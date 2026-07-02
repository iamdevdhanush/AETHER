import asyncio, httpx

async def test():
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post("http://localhost:11434/api/chat", json={
            "model": "deepseek-coder",
            "messages": [{"role": "user", "content": "hello"}],
            "stream": False
        })
        print(f"Status: {r.status_code}")
        print(f"Body: {r.text[:2000]}")
        
        r2 = await client.post("http://localhost:11434/api/generate", json={
            "model": "deepseek-coder",
            "prompt": "hello",
            "stream": False
        })
        print(f"\nGenerate Status: {r2.status_code}")
        print(f"Body: {r2.text[:2000]}")

asyncio.run(test())
