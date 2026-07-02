import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from services.ollama import LLMService

async def test():
    llm = LLMService()
    print(f"Base URL: {llm.base_url}")
    print(f"Model: {llm.model}")
    try:
        chunks = []
        async for chunk in llm.generate([{"role": "user", "content": "Say hello in one word"}], stream=True):
            chunks.append(chunk)
        result = "".join(chunks)
        print(f"Streaming result: {result}")
        if "Error" in result:
            print("OLLAMA CONNECTION FAILED")
        else:
            print("OLLAMA OK")
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    await llm.close()

asyncio.run(test())
