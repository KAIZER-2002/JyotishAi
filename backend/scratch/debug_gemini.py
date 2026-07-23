import sys
import asyncio
from google import genai
from google.genai.errors import APIError
from app.core.config import settings

async def main():
    try:
        import google.genai as genai_pkg
        sdk_version = getattr(genai_pkg, '__version__', 'unknown (2.10.0 from reqs)')
    except Exception as e:
        sdk_version = str(e)
    
    # 2. Configured Model
    configured_model = settings.GEMINI_EMBEDDING_MODEL
    
    client = genai.Client()
    
    # API Version
    # Under new google-genai, api_version is often internal or accessed via http_options
    try:
        api_version = client._api_client.api_version if hasattr(client, '_api_client') else 'v1alpha (default fallback)'
    except Exception as e:
        api_version = 'unknown'

    print("=== Diagnostics ===")
    print(f"SDK Version: {sdk_version}")
    print(f"Configured Model: {configured_model}")
    print(f"API Version: {api_version}")
    
    # Models list
    try:
        models = [m.name for m in client.models.list_models() if 'embed' in m.name.lower()]
        print(f"Available Embedding Models: {models}")
    except Exception as e:
        print(f"Available Embedding Models: Failed to list - {e}")
        
    print(f"Embedding Endpoint: /v1beta/models/{configured_model}:embedContent (implied by SDK)")

    print("\n--- Testing embed_content ---")
    try:
        response = await client.aio.models.embed_content(
            model=configured_model,
            contents=["Test document chunk"]
        )
        print("Raw Response:", response)
    except APIError as e:
        print("Raw Response: None (Exception raised)")
        print("HTTP Status Code:", e.code)
        print("Response Body:", e.message)
        print("FULL Exception:", repr(e))
    except Exception as e:
        print("Raw Response: None")
        print("FULL Exception:", repr(e))

if __name__ == "__main__":
    asyncio.run(main())
