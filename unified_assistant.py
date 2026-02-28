"""
Unified Voice-Enabled Apartment Search Assistant
Combines: Voice Input + Yutori + Pioneer + Reka
"""
import os
import time
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import requests
from yutori import YutoriClient

load_dotenv()

app = Flask(__name__)
CORS(app)

# API Keys
YUTORI_API_KEY = os.getenv("YUTORI_API_KEY")
PIONEER_API_KEY = os.getenv("PIONEER_API_KEY")
REKA_API_KEY = os.getenv("REKA_API_KEY")

yutori_client = YutoriClient(api_key=YUTORI_API_KEY)

# Store current property data
current_property = {
    "extraction": None,
    "insights": None,
    "structured_data": None
}

user_preferences = {}

@app.route('/')
def index():
    return render_template('assistant.html')

@app.route('/api/set-preferences', methods=['POST'])
def set_preferences():
    """Store user preferences"""
    global user_preferences
    data = request.json
    user_preferences = {
        "budget": data.get('budget', 'Not specified'),
        "bedrooms": data.get('bedrooms', 'Not specified'),
        "must_haves": data.get('must_haves', 'Not specified'),
        "lifestyle": data.get('lifestyle', 'Not specified'),
        "priorities": data.get('priorities', 'Not specified')
    }
    return jsonify({"status": "success", "preferences": user_preferences})

@app.route('/api/search-property', methods=['POST'])
def search_property():
    """Use Yutori to extract property data"""
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({"error": "URL required"}), 400

    try:
        print(f"🔍 Extracting data from: {url}")

        # Use Yutori to extract property data
        task = yutori_client.browsing.create(
            task="""Extract ALL apartment information including:
            - Property name, address, phone
            - All pricing and floor plans
            - All amenities
            - Description and lease terms
            - Virtual tour and photo URLs""",
            start_url=url,
            max_steps=30
        )

        task_id = task.get('task_id')
        view_url = task.get('view_url')

        # Poll for completion
        for i in range(60):
            time.sleep(3)
            result = yutori_client.browsing.get(task_id)
            status = result.get('status')

            if status == 'succeeded':
                extraction_data = result.get('result', '')

                # Save extraction
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                extraction_file = Path(f"extractions/property_{timestamp}.txt")
                extraction_file.parent.mkdir(exist_ok=True)
                extraction_file.write_text(extraction_data)

                current_property['extraction'] = extraction_data

                return jsonify({
                    "status": "success",
                    "extraction": extraction_data[:500] + "...",
                    "yutori_url": view_url,
                    "file": str(extraction_file)
                })
            elif status == 'failed':
                return jsonify({"error": "Extraction failed"}), 500

        return jsonify({"error": "Extraction timeout"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/extract-structured', methods=['POST'])
def extract_structured():
    """Use Pioneer GLiNER-2 to extract structured entities"""
    if not current_property['extraction']:
        return jsonify({"error": "No extraction data available"}), 400

    try:
        # Use Pioneer to extract key entities
        response = requests.post(
            "https://api.pioneer.ai/gliner-2",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": PIONEER_API_KEY
            },
            json={
                "task": "extract_entities",
                "text": current_property['extraction'][:2000],  # First 2000 chars
                "schema": [
                    "property_name",
                    "address",
                    "phone_number",
                    "price",
                    "bedroom_count",
                    "amenity"
                ],
                "threshold": 0.5
            },
            timeout=30
        )

        if response.status_code == 200:
            structured_data = response.json()
            current_property['structured_data'] = structured_data
            return jsonify({
                "status": "success",
                "data": structured_data
            })
        else:
            return jsonify({"error": f"Pioneer API error: {response.status_code}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-insights', methods=['POST'])
def generate_insights():
    """Use Reka to generate property insights"""
    if not current_property['extraction']:
        return jsonify({"error": "No extraction data available"}), 400

    try:
        user_prefs = f"""
USER PREFERENCES:
Budget: ${user_preferences.get('budget', 'Not specified')}/month
Bedrooms: {user_preferences.get('bedrooms', 'Not specified')}
Must-have amenities: {user_preferences.get('must_haves', 'Not specified')}
Lifestyle: {user_preferences.get('lifestyle', 'Not specified')}
Priorities: {user_preferences.get('priorities', 'Not specified')}
"""

        prompt = f"""You are a real estate analyst. Analyze this apartment listing and provide insights.

{user_prefs}

PROPERTY DATA:
{current_property['extraction']}

Provide:
1. EXECUTIVE SUMMARY (2-3 sentences)
2. PRICING ANALYSIS (best value, most expensive)
3. TOP 5 AMENITIES
4. MATCH WITH USER PREFERENCES (how well does it fit?)
5. RECOMMENDATIONS (should they rent here?)
6. CONCERNS (any red flags?)

Be specific and data-driven."""

        response = requests.post(
            "https://api.reka.ai/v1/chat",
            headers={
                "X-Api-Key": REKA_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "model": "reka-core",
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=120
        )

        if response.status_code == 200:
            insights = response.json()['responses'][0]['message']['content']
            current_property['insights'] = insights
            return jsonify({
                "status": "success",
                "insights": insights
            })
        else:
            return jsonify({"error": f"Reka API error: {response.status_code}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ask-question', methods=['POST'])
def ask_question():
    """Answer questions using Reka AI"""
    data = request.json
    question = data.get('question')

    if not question:
        return jsonify({"error": "Question required"}), 400

    if not current_property['extraction']:
        return jsonify({"error": "No property data loaded"}), 400

    try:
        user_prefs = f"""
USER PREFERENCES:
Budget: ${user_preferences.get('budget', 'Not specified')}/month
Bedrooms: {user_preferences.get('bedrooms', 'Not specified')}
Must-have amenities: {user_preferences.get('must_haves', 'Not specified')}
Lifestyle: {user_preferences.get('lifestyle', 'Not specified')}
Priorities: {user_preferences.get('priorities', 'Not specified')}
"""

        prompt = f"""You are a helpful real estate assistant.

{user_prefs}

PROPERTY DATA:
{current_property['extraction']}

INSIGHTS:
{current_property.get('insights', 'Not generated yet')}

User Question: {question}

Provide a helpful, personalized answer based on their preferences and the property data."""

        response = requests.post(
            "https://api.reka.ai/v1/chat",
            headers={
                "X-Api-Key": REKA_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "model": "reka-core",
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )

        if response.status_code == 200:
            answer = response.json()['responses'][0]['message']['content']
            return jsonify({
                "status": "success",
                "answer": answer
            })
        else:
            return jsonify({"error": f"Reka API error: {response.status_code}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 UNIFIED APARTMENT ASSISTANT")
    print("="*70)
    print("\nFeatures:")
    print("  🎤 Voice Input (browser-based)")
    print("  🔍 Yutori Web Scraping")
    print("  📊 Pioneer Structured Extraction")
    print("  🤖 Reka AI Insights & Q&A")
    print(f"\n🌐 Opening at: http://localhost:5002")
    print("="*70 + "\n")

    app.run(debug=True, port=5002, host='0.0.0.0')
