import asyncio, httpx

async def test():
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Try root
        try:
            r = await client.get("http://localhost:11434/")
            print(f"Root: {r.status_code} {r.text[:200]}")
        except Exception as e:
            print(f"Root error: {e}")
        
        # Try /api/tags
        try:
            r = await client.get("http://localhost:11434/api/tags")
            print(f"Tags: {r.status_code} {r.text[:500]}")
        except Exception as e:
            print(f"Tags error: {e}")
        
        # Try /api/generate with prompt
        try:
            async with client.stream("POST", "http://localhost:11434/api/generate", json={
                "model": "llama3.2",
                "prompt": "Say hello",
                "stream": True
            }) as resp:
                print(f"Generate status: {resp.status_code}")
                async for line in resp.aiter_lines():
                    if line.strip():
                        print(f"Line: {line[:200]}")
                        break
        except Exception as e:
            print(f"Generate error: {e}")

asyncio.run(test())
