"""Test Yutori API directly to debug the issue"""
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

YUTORI_API_KEY = os.getenv("YUTORI_API_KEY")
print(f"API Key: {YUTORI_API_KEY[:20]}..." if YUTORI_API_KEY else "No API key found")

async def test_yutori():
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("\nTesting Yutori API...")
            print("Endpoint: https://api.yutori.com/v1/browsing")

            response = await client.post(
                "https://api.yutori.com/v1/browsing",
                headers={
                    "Authorization": f"Bearer {YUTORI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "task": "Click the fullscreen button",
                    "start_url": "https://discover.matterport.com/space/geQebf1HNtN",
                    "max_steps": 10,
                    "agent": "navigator-n1-latest"
                }
            )

            print(f"\nStatus Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"\nResponse Body:")
            print(response.text)

            if response.status_code == 200:
                data = response.json()
                print(f"\nSession ID: {data.get('id')}")
            else:
                print(f"\nError: {response.status_code}")

    except Exception as e:
        print(f"\nException occurred: {type(e).__name__}")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_yutori())
