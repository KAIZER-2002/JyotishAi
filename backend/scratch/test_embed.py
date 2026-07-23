import asyncio
from google import genai
from google.genai import types
from google.genai.errors import APIError

async def run():
    client = genai.Client(http_options={'api_version': 'v1alpha'})
    try:
        r = await client.aio.models.embed_content(model='text-embedding-004', contents=['test'])
        print("Success v1alpha:", len(r.embeddings))
    except APIError as e:
        print(f"APIError v1alpha: {e}")

asyncio.run(run())
