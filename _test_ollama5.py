import asyncio, httpx, json

async def test():
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Try without stream first
        print("=== Testing /api/generate (no stream) ===")
        r = await client.post("http://localhost:11434/api/generate", json={
            "model": "llama3",
            "prompt": "Respond with just the word: Hello",
            "stream": False
        })
        print(f"Status: {r.status_code}")
        print(f"Body: {r.text[:1000]}")
        
        # List models
        r2 = await client.get("http://localhost:11434/api/tags")
        models = r2.json().get("models", [])
        print(f"\nAvailable models: {[m['name'] for m in models]}")

asyncio.run(test())
