import asyncio, httpx, json

async def test():
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test generate API with correct model
        print("=== Testing /api/generate with llama3 ===")
        try:
            async with client.stream("POST", "http://localhost:11434/api/generate", json={
                "model": "llama3",
                "prompt": "Respond with just the word: Hello",
                "stream": True
            }) as resp:
                print(f"Status: {resp.status_code}")
                full = ""
                async for line in resp.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            content = data.get("response", "")
                            full += content
                            if data.get("done"):
                                break
                        except json.JSONDecodeError as e:
                            print(f"JSON error: {line[:100]}")
                print(f"Result: '{full}'")
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(test())
