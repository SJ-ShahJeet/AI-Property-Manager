"""Check what data Yutori is actually returning"""
import os
from dotenv import load_dotenv
from yutori import YutoriClient
import json

load_dotenv()

client = YutoriClient(api_key=os.getenv("YUTORI_API_KEY"))

session_id = "5f33b4b9-bd65-4730-981e-6f86f27633db"

print(f"Fetching session: {session_id}")
result = client.browsing.get(session_id)

print("\n" + "="*60)
print("FULL API RESPONSE:")
print("="*60)
print(json.dumps(result, indent=2))

print("\n" + "="*60)
print("KEY FIELDS:")
print("="*60)
print(f"Status: {result.get('status')}")
print(f"Has 'screenshot' field: {'screenshot' in result}")
print(f"Has 'screenshots' field: {'screenshots' in result}")
print(f"Has 'recording_url' field: {'recording_url' in result}")
print(f"Has 'view_url' field: {'view_url' in result}")
print(f"Available keys: {list(result.keys())}")
