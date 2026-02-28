"""
Generate meaningful insights from apartment extraction using AI (Reka)
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import requests

load_dotenv()

# Use Reka API
REKA_API_KEY = os.getenv("REKA_API_KEY")

print("="*70)
print("🧠 PROPERTY INSIGHTS GENERATOR")
print("="*70)

# Read the extraction results
extraction_file = Path("extractions/hub_west_lafayette_20260227_150044.txt")
print(f"\n📖 Reading extraction from: {extraction_file}\n")

with open(extraction_file) as f:
    extraction_data = f.read()

# Generate insights using Reka AI
print("🤔 Analyzing property data with AI...\n")

response = requests.post(
    "https://api.reka.ai/v1/chat",
    headers={
        "X-Api-Key": REKA_API_KEY,
        "Content-Type": "application/json"
    },
    json={
        "model": "reka-core",
        "messages": [{
            "role": "user",
            "content": f"""You are a real estate analyst. Analyze this apartment listing extraction and provide meaningful insights.

EXTRACTION DATA:
{extraction_data}

Please provide:

## 1. EXECUTIVE SUMMARY
- Quick overview of the property (2-3 sentences)
- Key selling points

## 2. PRICING ANALYSIS
- Price range breakdown
- Value proposition (is it competitive?)
- Best value floor plans
- Most expensive options

## 3. AMENITY HIGHLIGHTS
- Top 5 most valuable amenities
- Unique features that set it apart
- Missing amenities (what don't they have?)

## 4. TARGET AUDIENCE
- Who is this property best suited for?
- Student features vs. professional features
- Lifestyle match

## 5. COMPETITIVE ADVANTAGES
- What makes this property stand out?
- Premium features worth the price

## 6. POTENTIAL CONCERNS
- Any red flags or limitations?
- What questions should renters ask?

## 7. RECOMMENDATIONS
- Who should rent here?
- Who should look elsewhere?
- Best floor plan for different budgets

## 8. KEY METRICS SUMMARY
Present in a table format:
- Unit types available
- Price per sq ft analysis
- Amenity count
- Lease flexibility

Be specific, data-driven, and actionable. Use numbers from the extraction."""
        }]
    },
    timeout=120
)

if response.status_code == 200:
    insights = response.json()['responses'][0]['message']['content']
else:
    print(f"Error: {response.status_code}")
    print(response.text)
    exit(1)

# Save insights
insights_file = Path("extractions/insights_hub_west_lafayette.md")
with open(insights_file, "w") as f:
    f.write(f"""# Property Insights: Hub on Campus West Lafayette

**Generated:** 2026-02-27
**Source:** Apartments.com
**AI Analysis by:** Claude 3.5 Sonnet

---

{insights}

---

## Data Source
- **Extraction:** {extraction_file}
- **Property URL:** https://www.apartments.com/hub-on-campus-west-lafayette-west-lafayette-in/69yh6bv/
- **Yutori Recording:** https://platform.yutori.com/browsing/tasks/2d34c205-3f38-4f48-aa08-61794f126124
""")

print("="*70)
print("✨ INSIGHTS GENERATED")
print("="*70)
print(insights)
print("\n" + "="*70)
print(f"📄 Saved to: {insights_file.absolute()}")
print("="*70)

# Also create a JSON summary
json_insights = {
    "property_name": "Hub on Campus West Lafayette",
    "analysis_date": "2026-02-27",
    "price_range": "$1,145 - $2,329 per person",
    "unit_types": "Studio - 4 bedrooms",
    "insights_file": str(insights_file),
    "extraction_file": str(extraction_file),
    "insights_preview": insights[:500] + "..."
}

with open("extractions/insights_summary.json", "w") as f:
    json.dump(json_insights, f, indent=2)

print(f"\n📊 Summary saved to: extractions/insights_summary.json")
