"""Test different Yutori authentication methods"""
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

YUTORI_API_KEY = os.getenv("YUTORI_API_KEY")
print(f"API Key loaded: {bool(YUTORI_API_KEY)}")
print(f"API Key prefix: {YUTORI_API_KEY[:10]}..." if YUTORI_API_KEY else "None")

async def test_auth_methods():
    """Try different authentication methods"""

    methods = [
        {
            "name": "Bearer token (current)",
            "headers": {
                "Authorization": f"Bearer {YUTORI_API_KEY}",
                "Content-Type": "application/json"
            }
        },
        {
            "name": "X-Api-Key header",
            "headers": {
                "X-Api-Key": YUTORI_API_KEY,
                "Content-Type": "application/json"
            }
        },
        {
            "name": "Authorization without Bearer",
            "headers": {
                "Authorization": YUTORI_API_KEY,
                "Content-Type": "application/json"
            }
        }
    ]

    # Test with a simple endpoint first - try to list/get info
    test_endpoints = [
        ("POST", "https://api.yutori.com/v1/browsing", {
            "task": "Navigate to the page",
            "start_url": "https://example.com",
            "max_steps": 5
        }),
        ("GET", "https://api.yutori.com/v1/browsing", None),
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        for method_info in methods:
            print(f"\n{'='*60}")
            print(f"Testing: {method_info['name']}")
            print(f"{'='*60}")

            for http_method, endpoint, data in test_endpoints:
                try:
                    print(f"\n{http_method} {endpoint}")

                    if http_method == "POST":
                        response = await client.post(
                            endpoint,
                            headers=method_info['headers'],
                            json=data
                        )
                    else:
                        response = await client.get(
                            endpoint,
                            headers=method_info['headers']
                        )

                    print(f"Status: {response.status_code}")
                    print(f"Response: {response.text[:200]}")

                    if response.status_code == 200:
                        print("✅ SUCCESS!")
                        return

                except Exception as e:
                    print(f"Error: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_auth_methods())
