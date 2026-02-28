"""
Extract complete apartment information from Apartments.com
Including photos, pricing, amenities, floor plans, and more
"""
import os
import time
import httpx
from pathlib import Path
from dotenv import load_dotenv
from yutori import YutoriClient
from pydantic import BaseModel
from typing import List, Optional

load_dotenv()

class ApartmentInfo(BaseModel):
    """Complete apartment information"""
    property_name: str
    address: str
    pricing: str
    bedrooms: str
    bathrooms: str
    square_footage: Optional[str] = None
    amenities: List[str]
    description: str
    photo_urls: List[str]
    floor_plan_urls: List[str]
    contact_phone: Optional[str] = None
    website_url: Optional[str] = None
    virtual_tour_url: Optional[str] = None
    pet_policy: Optional[str] = None
    lease_terms: Optional[str] = None

# Initialize
client = YutoriClient(api_key=os.getenv("YUTORI_API_KEY"))

print("="*70)
print("🏠 APARTMENTS.COM INFORMATION EXTRACTOR")
print("="*70)

# Use the working listing Yutori found
apartment_url = "https://www.apartments.com/hub-on-campus-west-lafayette-west-lafayette-in/69yh6bv/"

print(f"\n🔍 Extracting from: {apartment_url}\n")

# Extract all information
print("Step 1: Extracting apartment information...")
print("-" * 70)

task = client.browsing.create(
    task=f"""
    Extract ALL available information from this Apartments.com listing.

    Please gather:

    **Basic Information:**
    - Property name
    - Full address
    - Pricing (rent range or specific price)
    - Number of bedrooms
    - Number of bathrooms
    - Square footage

    **Amenities:**
    - List ALL amenities mentioned (both property and unit amenities)

    **Media:**
    - Extract ALL photo URLs (look for img tags, gallery images, etc.)
    - Extract floor plan image URLs if available
    - Find virtual tour links if available

    **Contact & Details:**
    - Contact phone number
    - Website URL
    - Pet policy details
    - Lease terms

    **Description:**
    - Full property description

    Be thorough - extract everything you can find on the page!
    Click through photo galleries if needed to get all image URLs.
    """,
    start_url=apartment_url,
    output_schema=ApartmentInfo,
    max_steps=50  # Give it plenty of steps to explore
)

task_id = task.get('task_id')
view_url = task.get('view_url')

print(f"✅ Task created: {task_id}")
print(f"📺 Watch live: {view_url}\n")

# Poll for completion
print("⏳ Waiting for extraction...")
for i in range(100):  # Increased timeout
    time.sleep(3)
    result = client.browsing.get(task_id)
    status = result.get('status')

    if status == 'queued':
        print(f"  [{i+1}] Queued...")
    elif status == 'running':
        print(f"  [{i+1}] Extracting information...")
    elif status == 'succeeded':
        print(f"\n✅ Extraction complete!\n")
        break
    elif status == 'failed':
        print(f"\n❌ Task failed: {result.get('error')}")
        exit(1)
else:
    print("\n⚠️  Task timed out")
    exit(1)

# Display results
print("="*70)
print("📊 APARTMENT INFORMATION")
print("="*70)

if 'output' in result:
    info = result['output']

    print(f"\n🏢 PROPERTY: {info.get('property_name')}")
    print(f"📍 ADDRESS: {info.get('address')}")
    print(f"💰 PRICING: {info.get('pricing')}")
    print(f"🛏️  BEDROOMS: {info.get('bedrooms')}")
    print(f"🚿 BATHROOMS: {info.get('bathrooms')}")
    if info.get('square_footage'):
        print(f"📐 SIZE: {info.get('square_footage')}")

    print(f"\n📝 DESCRIPTION:")
    print(f"{info.get('description')}")

    print(f"\n✨ AMENITIES ({len(info.get('amenities', []))}):")
    for amenity in info.get('amenities', []):
        print(f"  • {amenity}")

    if info.get('pet_policy'):
        print(f"\n🐕 PET POLICY: {info.get('pet_policy')}")

    if info.get('lease_terms'):
        print(f"\n📄 LEASE TERMS: {info.get('lease_terms')}")

    if info.get('contact_phone'):
        print(f"\n📞 CONTACT: {info.get('contact_phone')}")

    if info.get('website_url'):
        print(f"\n🌐 WEBSITE: {info.get('website_url')}")

    if info.get('virtual_tour_url'):
        print(f"\n🎬 VIRTUAL TOUR: {info.get('virtual_tour_url')}")

    # Photos
    photo_urls = info.get('photo_urls', [])
    print(f"\n📸 PHOTOS FOUND: {len(photo_urls)}")
    if photo_urls:
        print("\nPhoto URLs:")
        for i, url in enumerate(photo_urls[:10], 1):  # Show first 10
            print(f"  {i}. {url}")
        if len(photo_urls) > 10:
            print(f"  ... and {len(photo_urls) - 10} more")

    # Floor plans
    floor_plan_urls = info.get('floor_plan_urls', [])
    print(f"\n📐 FLOOR PLANS FOUND: {len(floor_plan_urls)}")
    if floor_plan_urls:
        print("\nFloor Plan URLs:")
        for i, url in enumerate(floor_plan_urls, 1):
            print(f"  {i}. {url}")

    # Download photos to images folder
    if photo_urls:
        print(f"\n" + "="*70)
        print("💾 DOWNLOADING PHOTOS")
        print("="*70)

        images_dir = Path("images") / "apartments"
        images_dir.mkdir(parents=True, exist_ok=True)

        downloaded = 0
        for i, url in enumerate(photo_urls, 1):
            try:
                print(f"  ⬇️  Downloading photo {i}/{len(photo_urls)}...")

                with httpx.Client(timeout=30.0) as http_client:
                    response = http_client.get(url, follow_redirects=True)
                    response.raise_for_status()

                    filename = f"photo_{i}.jpg"
                    filepath = images_dir / filename
                    filepath.write_bytes(response.content)

                    size_kb = len(response.content) // 1024
                    print(f"  ✅ Saved: {filename} ({size_kb} KB)")
                    downloaded += 1

            except Exception as e:
                print(f"  ❌ Failed to download photo {i}: {e}")

        print(f"\n✅ Downloaded {downloaded} photos to: {images_dir.absolute()}")

else:
    print("\n📝 RAW RESULT:")
    print(result.get('result', 'No structured output available'))

print(f"\n" + "="*70)
print("✨ EXTRACTION COMPLETE")
print("="*70)
print(f"📺 View full recording: {view_url}")
print("="*70)
