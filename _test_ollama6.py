import asyncio, httpx, json

async def test():
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Test deepseek-coder (1B model - should fit in VRAM)
        print("=== Testing /api/chat with deepseek-coder ===")
        try:
            async with client.stream("POST", "http://localhost:11434/api/chat", json={
                "model": "deepseek-coder",
                "messages": [{"role": "user", "content": "Respond with just the word: Hello"}],
                "stream": True
            }) as resp:
                print(f"Status: {resp.status_code}")
                full = ""
                async for line in resp.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            full += content
                            if data.get("done"):
                                break
                        except json.JSONDecodeError:
                            print(f"JSON error: {line[:100]}")
                print(f"Result: '{full}'")
        except Exception as e:
            print(f"Chat API error: {e}")
        
        # Also test generate API
        print("\n=== Testing /api/generate with deepseek-coder ===")
        try:
            async with client.stream("POST", "http://localhost:11434/api/generate", json={
                "model": "deepseek-coder",
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
                        except json.JSONDecodeError:
                            print(f"JSON error: {line[:100]}")
                print(f"Result: '{full}'")
        except Exception as e:
            print(f"Generate API error: {e}")

asyncio.run(test())
