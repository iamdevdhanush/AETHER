import asyncio, sys, os, json, httpx
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

async def test():
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "model": "llama3.2",
            "messages": [{"role": "user", "content": "Say hello in one word"}],
            "stream": True,
            "options": {"temperature": 0.7, "top_p": 0.9},
        }
        try:
            async with client.stream("POST", "http://localhost:11434/api/chat", json=payload) as resp:
                print(f"Status: {resp.status_code}")
                async for line in resp.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError as e:
                        print(f"JSON error: {e} | line: {line[:100]}")
                        continue
                    content = data.get("message", {}).get("content", "")
                    done = data.get("done", False)
                    print(f"Content: '{content}' done={done}")
        except Exception as e:
            print(f"Exception: {e}")
            import traceback
            traceback.print_exc()

asyncio.run(test())
