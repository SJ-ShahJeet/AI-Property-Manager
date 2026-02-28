"""
AI Property Assistant - Voice-Powered Apartment Search
Main application combining: Voice Orb → Yutori Search → Reka Analysis → Dashboard
"""
import os
import time
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import requests
from yutori import YutoriClient

load_dotenv()

app = Flask(__name__)
CORS(app)

# API Keys
YUTORI_API_KEY = os.getenv("YUTORI_API_KEY")
REKA_API_KEY = os.getenv("REKA_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

yutori_client = YutoriClient(api_key=YUTORI_API_KEY)

# Image folder
IMAGE_FOLDER = Path("/Users/jeetshah/Documents/testing image + interactions ")
IMAGE_DATA_FILE = IMAGE_FOLDER / "image_data.json"

# Load image data if available
image_database = {}
if IMAGE_DATA_FILE.exists():
    with open(IMAGE_DATA_FILE) as f:
        image_database = json.load(f)

# Current session data
current_session = {
    "extraction": None,
    "insights": None,
    "property_url": None,
    "property_name": None,
    "images": []
}

@app.route('/')
def index():
    """Serve the voice-powered orb landing page"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Serve the property dashboard after search"""
    return render_template('dashboard.html')

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve images from the testing folder"""
    return send_from_directory(IMAGE_FOLDER, filename)

@app.route('/api/search-and-extract', methods=['POST'])
def search_and_extract():
    """
    Search for property using Tavily, then extract data with Yutori
    """
    data = request.json
    query = data.get('query')

    if not query:
        return jsonify({"error": "Query required"}), 400

    try:
        print(f"\n🔍 Searching for: {query}")

        # Step 1: Use Tavily to find the property URL
        tavily_response = requests.post(
            "https://api.tavily.com/search",
            headers={"Content-Type": "application/json"},
            json={
                "api_key": TAVILY_API_KEY,
                "query": f"{query} apartments",
                "search_depth": "basic",
                "max_results": 3
            },
            timeout=30
        )

        if tavily_response.status_code != 200:
            return jsonify({"error": f"Search failed: {tavily_response.status_code}"}), 500

        search_results = tavily_response.json()

        if not search_results.get('results'):
            return jsonify({"error": "No properties found"}), 404

        # Get the first result URL
        property_url = search_results['results'][0]['url']
        print(f"📍 Found property at: {property_url}")

        # Step 2: Use Yutori to extract property data
        print(f"🤖 Extracting data from: {property_url}")

        task = yutori_client.browsing.create(
            task="""Extract ALL apartment information including:
            - Property name, address, phone
            - All pricing and floor plans
            - All amenities and features
            - Description and lease terms
            - Virtual tour and photo URLs""",
            start_url=property_url,
            max_steps=30
        )

        task_id = task.get('task_id')
        view_url = task.get('view_url')

        # Poll for completion
        extraction_data = None
        for i in range(60):
            time.sleep(3)
            result = yutori_client.browsing.get(task_id)
            status = result.get('status')

            if status == 'succeeded':
                extraction_data = result.get('result', '')
                break
            elif status == 'failed':
                return jsonify({"error": "Extraction failed"}), 500

        if not extraction_data:
            return jsonify({"error": "Extraction timeout"}), 500

        # Save extraction
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extraction_file = Path(f"extractions/property_{timestamp}.txt")
        extraction_file.parent.mkdir(exist_ok=True)
        extraction_file.write_text(extraction_data)

        # Step 3: Generate insights with Reka
        print("🧠 Generating insights with Reka...")

        insights_prompt = f"""You are a real estate analyst. Analyze this apartment listing and provide insights.

PROPERTY DATA:
{extraction_data}

Provide:
1. EXECUTIVE SUMMARY (2-3 sentences)
2. PRICING ANALYSIS (price range and best value)
3. TOP 5 AMENITIES
4. TARGET AUDIENCE (who is this best for?)
5. RECOMMENDATIONS (pros and cons)

Be specific and data-driven."""

        reka_response = requests.post(
            "https://api.reka.ai/v1/chat",
            headers={
                "X-Api-Key": REKA_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "model": "reka-core",
                "messages": [{"role": "user", "content": insights_prompt}]
            },
            timeout=120
        )

        insights = ""
        if reka_response.status_code == 200:
            insights = reka_response.json()['responses'][0]['message']['content']
            insights_file = Path(f"extractions/insights_{timestamp}.md")
            insights_file.write_text(insights)
        else:
            insights = "Insights generation failed"

        # Store in session
        current_session['extraction'] = extraction_data
        current_session['insights'] = insights
        current_session['property_url'] = property_url
        current_session['property_name'] = query
        current_session['images'] = list(image_database.keys())  # Use existing images for now

        print("✅ Extraction and analysis complete!")

        return jsonify({
            "status": "success",
            "property_url": property_url,
            "yutori_url": view_url,
            "extraction_file": str(extraction_file),
            "insights_file": str(insights_file) if reka_response.status_code == 200 else None
        })

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/property-data')
def get_property_data():
    """Get current property data for dashboard"""
    # Load from files if session is empty
    extraction_data = current_session.get('extraction', '')
    insights_data = current_session.get('insights', '')

    if not extraction_data and EXTRACTION_FILE.exists():
        extraction_data = EXTRACTION_FILE.read_text()

    if not insights_data and INSIGHTS_FILE.exists():
        insights_data = INSIGHTS_FILE.read_text()

    return jsonify({
        "info": {
            "property": {"name": current_session.get('property_name', 'Hub on Campus West Lafayette')},
            "url": current_session.get('property_url', '')
        },
        "insights": insights_data,
        "extraction": extraction_data[:1000] + "..." if extraction_data else "",
        "images": current_session.get('images', list(image_database.keys()))
    })

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
        return find_image()
    else:
        # Answer question using Groq FREE model
        try:
            # Load data from files if not in session
            extraction_data = current_session.get('extraction', '')
            insights_data = current_session.get('insights', '')

            if not extraction_data and EXTRACTION_FILE.exists():
                extraction_data = EXTRACTION_FILE.read_text()

            if not insights_data and INSIGHTS_FILE.exists():
                insights_data = INSIGHTS_FILE.read_text()

            context = f"""PROPERTY: Hub on Campus West Lafayette

INSIGHTS:
{insights_data[:2000] if insights_data else 'No insights available'}

FULL DATA:
{extraction_data[:3000] if extraction_data else 'No data available'}

Answer the user's question concisely and helpfully based on this data."""

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",  # FREE Groq model
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

                # Check if answer mentions specific room types and show related image
                room_keywords = {
                    'kitchen': ['kitchen', 'cooking', 'appliance'],
                    'bathroom': ['bathroom', 'shower', 'bath'],
                    'bedroom': ['bedroom', 'bed', 'sleep'],
                    'living': ['living', 'lounge', 'common']
                }

                image_to_show = None
                for room_type, keywords in room_keywords.items():
                    if any(kw in answer.lower() for kw in keywords):
                        # Find matching image
                        for filename, img_data in image_database.items():
                            if room_type in img_data.get('description', '').lower():
                                image_to_show = {
                                    "filename": filename,
                                    "description": img_data.get('description')
                                }
                                break
                        if image_to_show:
                            break

                return jsonify({
                    "type": "answer",
                    "answer": answer,
                    "image": image_to_show  # Optional image based on answer content
                })
            else:
                return jsonify({"error": f"Groq API error: {response.status_code}"}), 500

        except Exception as e:
            return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🎤 AI PROPERTY ASSISTANT")
    print("="*70)
    print("\nFeatures:")
    print("  🌟 Voice-Powered Search Interface")
    print("  🔍 Tavily Web Search")
    print("  🤖 Yutori Property Extraction")
    print("  🧠 Reka AI Insights")
    print("  ⚡ Groq Fast Q&A")
    print(f"\n🌐 Open: http://localhost:5004")
    print("="*70 + "\n")

    app.run(debug=True, port=5004, host='0.0.0.0')
