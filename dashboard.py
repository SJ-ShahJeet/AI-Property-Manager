"""
Apartment Dashboard - Predefined property with images and voice Q&A
Combines: Extracted data + Image analysis (Reka) + Voice Q&A
"""
import os
import json
import base64
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
CORS(app)

# API Keys
REKA_API_KEY = os.getenv("REKA_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Load predefined property data
EXTRACTION_FILE = Path("extractions/hub_west_lafayette_20260227_150044.txt")
INSIGHTS_FILE = Path("extractions/insights_hub_west_lafayette.md")
PROPERTY_JSON = Path("property_summary.json")

# Load property data
with open(EXTRACTION_FILE) as f:
    property_data = f.read()

with open(INSIGHTS_FILE) as f:
    insights = f.read()

with open(PROPERTY_JSON) as f:
    property_info = json.load(f)

# Image folder from testing
IMAGE_FOLDER = Path("/Users/jeetshah/Documents/testing image + interactions ")
IMAGE_DATA_FILE = IMAGE_FOLDER / "image_data.json"

# Load image data if available
image_database = {}
if IMAGE_DATA_FILE.exists():
    with open(IMAGE_DATA_FILE) as f:
        image_database = json.load(f)

user_preferences = {
    "budget": "Not set",
    "bedrooms": "Not set",
    "must_haves": "Not set",
    "lifestyle": "Not set",
    "priorities": "Not set"
}

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve images from the testing folder"""
    return send_from_directory(IMAGE_FOLDER, filename)

@app.route('/api/property-data')
def get_property_data():
    """Get all property data"""
    return jsonify({
        "info": property_info,
        "insights": insights,
        "extraction": property_data[:1000] + "...",
        "images": list(image_database.keys())
    })

@app.route('/api/set-preferences', methods=['POST'])
def set_preferences():
    """Store user preferences"""
    global user_preferences
    data = request.json
    user_preferences.update(data)
    return jsonify({"status": "success", "preferences": user_preferences})

@app.route('/api/ask-question', methods=['POST'])
def ask_question():
    """Answer questions using Reka AI"""
    data = request.json
    question = data.get('question')

    if not question:
        return jsonify({"error": "Question required"}), 400

    try:
        user_prefs = f"""
USER PREFERENCES:
Budget: ${user_preferences.get('budget', 'Not set')}/month
Bedrooms: {user_preferences.get('bedrooms', 'Not set')}
Must-have amenities: {user_preferences.get('must_haves', 'Not set')}
Lifestyle: {user_preferences.get('lifestyle', 'Not set')}
Priorities: {user_preferences.get('priorities', 'Not set')}
"""

        prompt = f"""You are a helpful real estate assistant for Hub on Campus West Lafayette.

{user_prefs}

PROPERTY DATA:
{property_data}

INSIGHTS:
{insights}

User Question: {question}

Provide a helpful, personalized answer based on their preferences and the property data. Be concise and friendly."""

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

@app.route('/api/find-image', methods=['POST'])
def find_image():
    """Find best matching image based on query"""
    data = request.json
    query = data.get('query', '').lower()

    if not image_database:
        return jsonify({"error": "No images available"}), 404

    # Simple keyword matching
    best_match = None
    best_score = 0

    for filename, img_data in image_database.items():
        description = img_data.get('description', '').lower()
        score = 0

        # Check for keywords
        keywords = query.split()
        for keyword in keywords:
            if keyword in description or keyword in filename.lower():
                score += 1

        if score > best_score:
            best_score = score
            best_match = {
                "filename": filename,
                "path": img_data.get('path'),
                "description": img_data.get('description')
            }

    if not best_match:
        # Return first image if no match
        first_key = list(image_database.keys())[0]
        best_match = {
            "filename": first_key,
            "path": image_database[first_key].get('path'),
            "description": image_database[first_key].get('description')
        }

    return jsonify(best_match)

@app.route('/api/smart-query', methods=['POST'])
def smart_query():
    """Smart endpoint that either shows image or answers question using Groq"""
    data = request.json
    query = data.get('query', '').lower()

    if not query:
        return jsonify({"error": "Query required"}), 400

    # Check if asking to see an image
    image_keywords = ['show', 'see', 'look', 'view', 'display', 'picture', 'photo']
    is_image_request = any(keyword in query for keyword in image_keywords)

    if is_image_request:
        # Find and return image
        return find_image()
    else:
        # Answer question using Groq (super fast!)
        try:
            context = f"""PROPERTY: Hub on Campus West Lafayette

INSIGHTS:
{insights[:2000]}

FULL DATA:
{property_data[:3000]}

Answer the user's question concisely and helpfully based on this data."""

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mixtral-8x7b-32768",
                    "messages": [
                        {"role": "system", "content": context},
                        {"role": "user", "content": query}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500
                },
                timeout=10
            )

            if response.status_code == 200:
                answer = response.json()['choices'][0]['message']['content']
                return jsonify({
                    "type": "answer",
                    "answer": answer
                })
            else:
                return jsonify({"error": f"Groq API error: {response.status_code}"}), 500

        except Exception as e:
            return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🏠 APARTMENT DASHBOARD")
    print("="*70)
    print(f"\n📍 Property: {property_info.get('property', {}).get('name')}")
    print(f"📊 Insights: Loaded")
    print(f"🖼️  Images: {len(image_database)} available")
    print(f"\n🌐 Dashboard: http://localhost:5003")
    print("="*70 + "\n")

    app.run(debug=True, port=5003, host='0.0.0.0')
