import asyncio
import os
import sys

def load_env_manually():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip()

load_env_manually()

async def verify_gemini():
    print("Gemini:")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("FAIL Key missing in environment")
        return
    print("[OK] Loaded")
    
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
        
        # Check models
        try:
            models_list = list(client.models.list())
            models = [m.name for m in models_list]
            print("[OK] Authentication OK")
            print("[OK] Reachable")
            print(f"Available Gemini Models: {', '.join(models[:20])}")
        except Exception as e:
            print("FAIL Authentication failed")
            print(f"Reason: {repr(e)}")
            return
            
        # Check text-embedding-004
        try:
            resp = await client.aio.models.embed_content(model="text-embedding-004", contents=["test"])
            print("[OK] Model text-embedding-004 available (Embedding endpoint OK)")
        except Exception as e:
            print(f"FAIL Model text-embedding-004 failed: {repr(e)}")
            
        # Check gemini-2.5-flash
        try:
            resp = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=["Say hi"]
            )
            print("[OK] Model gemini-2.5-flash available (Chat endpoint OK)")
        except Exception as e:
            print(f"FAIL Model gemini-2.5-flash failed: {repr(e)}")
            
        # Check stream
        try:
            # Test stream
            stream = await client.aio.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=["Say hi"]
            )
            async for chunk in stream:
                pass
            print("[OK] Streaming endpoint OK")
        except Exception as e:
            print(f"FAIL Streaming endpoint failed: {repr(e)}")

    except ImportError:
        print("FAIL Google GenAI SDK not installed")

async def verify_openai():
    print("\nOpenAI:")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("FAIL Key missing in environment")
        return
    print("[OK] Loaded")
    
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)
        
        try:
            resp = await client.models.list()
            print("[OK] Authentication OK")
            print("[OK] Reachable")
        except Exception as e:
            print("FAIL Authentication failed")
            print(f"Reason: {repr(e)}")
            return
            
        try:
            resp = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=10
            )
            print("[OK] Model gpt-4o-mini available (Chat endpoint OK)")
        except Exception as e:
            print(f"FAIL Chat endpoint failed: {repr(e)}")
            
        try:
            resp = await client.embeddings.create(
                model="text-embedding-3-small",
                input="test"
            )
            print("[OK] Model text-embedding-3-small available (Embedding endpoint OK)")
        except Exception as e:
            print(f"FAIL Embedding endpoint failed: {repr(e)}")
            
    except ImportError:
        print("FAIL OpenAI SDK not installed")

async def verify_anthropic():
    print("\nAnthropic:")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("FAIL Key missing in environment")
        return
    print("[OK] Loaded")
    
    try:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=api_key)
        
        try:
            resp = await client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "hi"}]
            )
            print("[OK] Authentication OK")
            print("[OK] Reachable")
            print("[OK] Model claude-3-haiku-20240307 available (Chat endpoint OK)")
        except Exception as e:
            print("FAIL Authentication or Chat failed")
            print(f"Reason: {repr(e)}")
            
    except ImportError:
        print("FAIL Anthropic SDK not installed")

async def verify_openrouter():
    print("\nOpenRouter:")
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("FAIL Key missing in environment")
        return
    print("[OK] Loaded")
    
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
        
        try:
            resp = await client.models.list()
            print("[OK] Authentication OK")
            print("[OK] Reachable")
        except Exception as e:
            print("FAIL Authentication failed")
            print(f"Reason: {repr(e)}")
            return
            
        try:
            resp = await client.chat.completions.create(
                model="google/gemini-flash-1.5",
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=10
            )
            print("✓ Model google/gemini-flash-1.5 available (Chat endpoint OK)")
        except Exception as e:
            print(f"✗ Chat endpoint failed: {repr(e)}")
            
    except ImportError:
        print("✗ OpenAI SDK not installed for OpenRouter")

async def main():
    await verify_gemini()
    await verify_openai()
    await verify_anthropic()
    await verify_openrouter()

if __name__ == "__main__":
    asyncio.run(main())
