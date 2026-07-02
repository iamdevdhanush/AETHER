import asyncio, httpx

async def test():
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.get("http://localhost:11434/api/tags")
        models = r.json().get("models", [])
        for m in models:
            print(f"  {m['name']}  ({m['details'].get('parameter_size','?')})")

asyncio.run(test())
