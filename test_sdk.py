"""Test Yutori SDK"""
import os
from dotenv import load_dotenv
from yutori import YutoriClient
import time

load_dotenv()

# Initialize client
print("Initializing Yutori client...")
client = YutoriClient(api_key=os.getenv("YUTORI_API_KEY"))

print("\nCreating browsing task...")
try:
    task = client.browsing.create(
        task="Click the fullscreen button if available, then wait and stay on the page so I can see the virtual tour.",
        start_url="https://discover.matterport.com/space/geQebf1HNtN",
        max_steps=10
    )

    print(f"✅ Task created successfully!")
    print(f"Task ID: {task.get('id') or task.get('task_id')}")
    print(f"Full response: {task}")

    # Poll for updates
    task_id = task.get('id') or task.get('task_id')
    print(f"\nPolling for updates on task {task_id}...")

    for i in range(20):
        time.sleep(3)
        result = client.browsing.get(task_id)
        status = result.get('status', 'unknown')
        print(f"[{i+1}] Status: {status}")

        if status in ('succeeded', 'failed'):
            print(f"\n✅ Final result:")
            print(result)
            break

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
