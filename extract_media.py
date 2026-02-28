"""
Test extracting media from Matterport tour using Yutori
"""
import os
from dotenv import load_dotenv
from yutori import YutoriClient
from pydantic import BaseModel
from typing import List

load_dotenv()

class MediaExtraction(BaseModel):
    """Structured output for media extraction"""
    image_urls: List[str]
    video_urls: List[str]
    tour_title: str
    description: str

# Initialize client
client = YutoriClient(api_key=os.getenv("YUTORI_API_KEY"))

print("Creating media extraction task...")
print("This will have Yutori extract all photos and videos from the tour\n")

task = client.browsing.create(
    task="""
    Extract all media from this Matterport virtual tour:
    1. Find the tour title/property name
    2. Look for any image URLs in the page source (check for img tags, background images, etc.)
    3. Look for any video URLs or video elements
    4. If there's a gallery or photo section, navigate to it and extract those URLs
    5. Return all the image and video URLs you find

    Return structured data with:
    - image_urls: list of all image URLs found
    - video_urls: list of all video URLs found
    - tour_title: the property/tour name
    - description: brief description of what you found
    """,
    start_url="https://discover.matterport.com/space/geQebf1HNtN",
    output_schema=MediaExtraction,
    max_steps=30
)

print(f"✅ Task created: {task.get('task_id')}")
print(f"📺 Watch at: {task.get('view_url')}")
print("\nWaiting for completion...")

# Poll for completion
import time
for i in range(60):
    time.sleep(3)
    result = client.browsing.get(task.get('task_id'))
    status = result.get('status')
    print(f"[{i+1}] Status: {status}")

    if status == 'succeeded':
        print("\n" + "="*60)
        print("✅ SUCCESS! Media extracted:")
        print("="*60)
        print(f"\nResult: {result.get('result')}")

        # The structured output should be in the result
        if 'output' in result:
            output = result['output']
            print(f"\nTour Title: {output.get('tour_title')}")
            print(f"\nDescription: {output.get('description')}")
            print(f"\nImage URLs found: {len(output.get('image_urls', []))}")
            for url in output.get('image_urls', [])[:10]:  # Show first 10
                print(f"  - {url}")
            print(f"\nVideo URLs found: {len(output.get('video_urls', []))}")
            for url in output.get('video_urls', [])[:10]:
                print(f"  - {url}")
        break
    elif status == 'failed':
        print(f"\n❌ Task failed: {result.get('error')}")
        break

print(f"\n📺 Full recording: {result.get('view_url')}")
