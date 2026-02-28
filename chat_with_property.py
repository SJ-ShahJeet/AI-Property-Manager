"""
Real-time Q&A about apartment properties using Reka AI
"""
import os
from dotenv import load_dotenv
import requests
from pathlib import Path

load_dotenv()

REKA_API_KEY = os.getenv("REKA_API_KEY")

# Load the extraction data
extraction_file = Path("extractions/hub_west_lafayette_20260227_150044.txt")
with open(extraction_file) as f:
    property_data = f.read()

# Load the insights
insights_file = Path("extractions/insights_hub_west_lafayette.md")
with open(insights_file) as f:
    insights = f.read()

print("="*70)
print("🏠 PROPERTY Q&A ASSISTANT")
print("="*70)
print(f"\nLoaded data for: Hub on Campus West Lafayette")
print("\nFirst, let me learn about your preferences!")
print("="*70)

# Collect user preferences
print("\n📋 Tell me what matters to you (press Enter to skip):\n")

budget = input("💰 Max budget per month: $").strip() or "Not specified"
bedrooms = input("🛏️  Number of bedrooms needed: ").strip() or "Not specified"
must_haves = input("✨ Must-have amenities (comma separated): ").strip() or "Not specified"
lifestyle = input("🎯 Lifestyle (student/professional/quiet/social): ").strip() or "Not specified"
priorities = input("🎨 Top priorities (location/price/amenities/space): ").strip() or "Not specified"

user_preferences = f"""
BUDGET: ${budget}/month
BEDROOMS: {bedrooms}
MUST-HAVE AMENITIES: {must_haves}
LIFESTYLE: {lifestyle}
PRIORITIES: {priorities}
"""

print("\n✅ Got it! Now you can ask questions and I'll answer based on your preferences.")
print("\nExample questions:")
print("  • Is this a good fit for me?")
print("  • What floor plan do you recommend?")
print("  • Are there any concerns I should know about?")
print("\nType 'quit' or 'exit' to stop.\n")
print("="*70)

# Chat loop
conversation_history = []

while True:
    user_question = input("\n💬 You: ").strip()

    if user_question.lower() in ['quit', 'exit', 'q']:
        print("\n👋 Goodbye!")
        break

    if not user_question:
        continue

    # Build context with conversation history - Reka format
    conversation_context = ""
    for msg in conversation_history[-6:]:  # Keep last 3 exchanges
        role = "User" if msg["role"] == "user" else "Assistant"
        conversation_context += f"\n{role}: {msg['content']}\n"

    # Build the full prompt with context
    full_prompt = f"""You are a helpful real estate assistant. You have access to detailed information about Hub on Campus West Lafayette apartment complex.

USER PREFERENCES:
{user_preferences}

PROPERTY DATA:
{property_data}

INSIGHTS:
{insights}

Answer questions accurately based on this data AND the user's preferences. Give personalized recommendations that match their budget, lifestyle, and priorities. Be friendly, concise, and helpful.

{conversation_context}

User: {user_question}
Assistant:"""

    messages = [{
        "role": "user",
        "content": full_prompt
    }]

    print("\n🤔 Thinking...")

    try:
        response = requests.post(
            "https://api.reka.ai/v1/chat",
            headers={
                "X-Api-Key": REKA_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "model": "reka-core",
                "messages": messages
            },
            timeout=30
        )

        if response.status_code == 200:
            answer = response.json()['responses'][0]['message']['content']
            print(f"\n🤖 Assistant: {answer}")

            # Save to conversation history
            conversation_history.append({"role": "user", "content": user_question})
            conversation_history.append({"role": "assistant", "content": answer})
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

print("\n" + "="*70)
