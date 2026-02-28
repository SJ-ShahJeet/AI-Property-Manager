"""
Extract photos and videos from Matterport tour and save to images folder
"""
import os
import time
import httpx
from pathlib import Path
from dotenv import load_dotenv
from yutori import YutoriClient
from pydantic import BaseModel
from typing import List
from urllib.parse import urlparse

load_dotenv()

class MediaExtraction(BaseModel):
    """Structured output for media extraction"""
    image_urls: List[str]
    video_urls: List[str]
    tour_title: str
    description: str

# Initialize
client = YutoriClient(api_key=os.getenv("YUTORI_API_KEY"))
images_dir = Path("images")
images_dir.mkdir(exist_ok=True)

print("="*60)
print("🎬 MATTERPORT MEDIA EXTRACTOR")
print("="*60)
print(f"\n📁 Saving to: {images_dir.absolute()}\n")

# Step 1: Extract media URLs using Yutori
print("Step 1: Extracting media URLs from tour...")
print("-" * 60)

task = client.browsing.create(
    task="""
    Extract all media from this Matterport virtual tour:

    1. Find the tour title/property name from the page
    2. Look for image URLs:
       - Check all <img> tags and their src attributes
       - Look for background-image in CSS
       - Find any data-src or srcset attributes
       - Look for thumbnail images
       - Check for any photo gallery links

    3. Look for video URLs:
       - Check <video> tags and their src
       - Look for embedded video players
       - Find any video file URLs

    4. Try to find the highest resolution versions available

    Return all unique URLs you find, focusing on the actual media files.
    """,
    start_url="https://discover.matterport.com/space/geQebf1HNtN",
    output_schema=MediaExtraction,
    max_steps=30
)

task_id = task.get('task_id')
view_url = task.get('view_url')

print(f"✅ Task created: {task_id}")
print(f"📺 Watch live: {view_url}\n")

# Poll for completion
print("⏳ Waiting for Yutori to extract media...")
for i in range(60):
    time.sleep(3)
    result = client.browsing.get(task_id)
    status = result.get('status')

    if status == 'queued':
        print(f"  [{i+1}] Queued...")
    elif status == 'running':
        print(f"  [{i+1}] Running...")
    elif status == 'succeeded':
        print(f"\n✅ Extraction complete!\n")
        break
    elif status == 'failed':
        print(f"\n❌ Task failed: {result.get('error')}")
        exit(1)
else:
    print("\n⚠️  Task timed out")
    exit(1)

# Step 2: Parse the results
print("-" * 60)
print("Step 2: Processing extracted URLs...")
print("-" * 60)

image_urls = []
video_urls = []
tour_title = "unknown_tour"

# Check if structured output is available
if 'output' in result:
    output = result['output']
    image_urls = output.get('image_urls', [])
    video_urls = output.get('video_urls', [])
    tour_title = output.get('tour_title', 'unknown_tour')
    description = output.get('description', '')

    print(f"\n📝 Tour: {tour_title}")
    print(f"📝 Description: {description}")
    print(f"\n📸 Found {len(image_urls)} images")
    print(f"🎥 Found {len(video_urls)} videos")
else:
    # Parse from text result
    result_text = result.get('result', '')
    print(f"\nResult text:\n{result_text[:500]}...\n")

    # Try to extract URLs from text
    import re
    urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', result_text)

    for url in urls:
        ext = Path(urlparse(url).path).suffix.lower()
        if ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
            image_urls.append(url)
        elif ext in ['.mp4', '.webm', '.mov', '.avi']:
            video_urls.append(url)

    print(f"📸 Extracted {len(image_urls)} image URLs from text")
    print(f"🎥 Extracted {len(video_urls)} video URLs from text")

# Step 3: Download media
print("\n" + "-" * 60)
print("Step 3: Downloading media files...")
print("-" * 60)

downloaded_count = 0

def download_file(url: str, folder: Path, prefix: str = ""):
    """Download a file from URL to folder"""
    try:
        filename = Path(urlparse(url).path).name
        if not filename:
            filename = f"{prefix}_{hash(url)}.jpg"

        filepath = folder / filename

        # Skip if already exists
        if filepath.exists():
            print(f"  ⏭️  Skipping (exists): {filename}")
            return False

        print(f"  ⬇️  Downloading: {filename}")

        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, follow_redirects=True)
            response.raise_for_status()

            filepath.write_bytes(response.content)
            print(f"  ✅ Saved: {filename} ({len(response.content) // 1024} KB)")
            return True

    except Exception as e:
        print(f"  ❌ Failed: {url[:50]}... - {e}")
        return False

# Download images
if image_urls:
    print(f"\n📸 Downloading {len(image_urls)} images...")
    for i, url in enumerate(image_urls, 1):
        if download_file(url, images_dir, f"image_{i}"):
            downloaded_count += 1

# Download videos
if video_urls:
    print(f"\n🎥 Downloading {len(video_urls)} videos...")
    videos_dir = images_dir / "videos"
    videos_dir.mkdir(exist_ok=True)

    for i, url in enumerate(video_urls, 1):
        if download_file(url, videos_dir, f"video_{i}"):
            downloaded_count += 1

# Summary
print("\n" + "="*60)
print("📊 SUMMARY")
print("="*60)
print(f"✅ Downloaded: {downloaded_count} files")
print(f"📁 Location: {images_dir.absolute()}")
print(f"📺 View extraction: {view_url}")
print("="*60)

# List downloaded files
print(f"\n📂 Files in {images_dir}:")
for file in sorted(images_dir.glob('*')):
    if file.is_file():
        size_kb = file.stat().st_size // 1024
        print(f"  - {file.name} ({size_kb} KB)")

if (images_dir / "videos").exists():
    print(f"\n📂 Videos in {images_dir / 'videos'}:")
    for file in sorted((images_dir / "videos").glob('*')):
        if file.is_file():
            size_kb = file.stat().st_size // 1024
            print(f"  - {file.name} ({size_kb} KB)")

print("\n✨ Done!")
