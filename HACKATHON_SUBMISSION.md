# AI Virtual Tour - Hackathon Submission

## Inspiration

Finding the perfect apartment is overwhelming. Students and renters spend hours browsing countless listings, comparing amenities, and trying to visualize spaces through static photos. Traditional apartment search platforms require tedious clicking through multiple pages, reading dense text descriptions, and struggling to remember details across different properties.

We envisioned a future where you could simply speak to an intelligent assistant and have it instantly retrieve, analyze, and explain apartment listings through natural conversation. Instead of reading through pages of information, what if you could just ask "How much is a two-bedroom?" or "Show me the kitchen" and get immediate visual and spoken responses?

This vision led us to build AI Virtual Tour - a voice-powered apartment search assistant that combines cutting-edge web automation, multi-modal AI analysis, and natural language processing to transform apartment hunting into an intuitive conversation.

## What it does

AI Virtual Tour is a voice-activated apartment search assistant that provides an entirely hands-free experience for exploring rental properties.

**Core Features:**

1. **Voice-Powered Search**: Users speak the property name, and the system automatically finds and extracts comprehensive data from apartment listing websites

2. **Intelligent Data Extraction**: Automatically gathers property details including:
   - Pricing and floor plans
   - Amenities and features
   - Contact information and location
   - Virtual tour links and photo galleries

3. **AI-Generated Insights**: Analyzes extracted data to provide:
   - Executive summaries
   - Pricing analysis and value assessment
   - Top amenities highlighting
   - Target audience recommendations
   - Pros and cons evaluation

4. **Conversational Q&A**: Users can ask questions naturally like:
   - "What's the price for a two-bedroom apartment?"
   - "Tell me about the amenities"
   - "Show me the kitchen"

5. **Smart Visual Display**: Automatically shows relevant property images based on conversation context - when discussing kitchens, the kitchen photo appears automatically

6. **Voice Responses**: All answers are spoken back to the user using natural text-to-speech, creating a fully voice-driven experience

The interface is minimalist by design - just a microphone button and a property image display, emphasizing the voice-first interaction paradigm.

## How we built it

AI Virtual Tour integrates five different AI services and APIs into a cohesive pipeline:

**Architecture:**

```
Voice Input → Tavily Search → Yutori Extraction → Pioneer Analysis → Reka Insights → Groq Q&A → Voice Output
```

**Technology Stack:**

1. **Frontend**:
   - Web Speech API for voice recognition (`webkitSpeechRecognition`)
   - SpeechSynthesis API for text-to-speech output
   - Vanilla JavaScript for state management (idle/listening/speaking states)
   - CSS3 animations for visual feedback

2. **Backend (Flask)**:
   - Python Flask server handling API orchestration
   - CORS enabled for cross-origin requests
   - File-based session persistence

3. **AI Services Integration**:

   - **Tavily API**: Web search to discover property URLs from natural language queries

   - **Yutori SDK**: Automated browser control for comprehensive data extraction from apartment listing websites. Configured with 30-step limit for thorough page navigation

   - **Pioneer (GLiNER-2)**: Entity extraction API from Fastino Labs for structured data parsing (person, organization, location entities)

   - **Reka AI**: Multi-modal AI model for image analysis and generating property insights from both visual and textual data

   - **Groq API**: Ultra-fast inference using `llama-3.3-70b-versatile` (free tier) for real-time conversational Q&A

**Key Implementation Details:**

- **Voice State Machine**: Implemented careful coordination between listening and speaking states to prevent the system from listening to its own voice output
- **Smart Image Matching**: Keyword-based algorithm matches user questions to relevant property photos by analyzing answer content
- **Session Recovery**: File-based persistence allows dashboard to load even when accessed directly without search
- **Async Processing**: 30-second animated loading sequence shows progress through extraction and analysis phases

**API Request Flow Example:**

When a user says "Hub on Campus West Lafayette":

1. Tavily searches for the property URL
2. Yutori navigates the site and extracts all structured data
3. Reka generates comprehensive insights from the extraction
4. Data is stored in `/extractions` folder
5. Dashboard loads with voice interface ready
6. Groq powers real-time Q&A using the extracted context

## Challenges we ran into

**1. WebGL Virtual Tour Extraction**

Our initial goal was to extract images directly from Matterport 3D virtual tours. However, Matterport uses WebGL rendering, meaning images are not available in the DOM as traditional `<img>` tags. All visual content is rendered programmatically to canvas elements.

*Solution*: Pivoted to extracting data from traditional apartment listing sites like Apartments.com that use structured HTML with accessible image URLs.

**2. API Authentication Complexity**

Initially attempted to use raw HTTP requests with Yutori API but encountered 403 Forbidden errors due to improper authentication header formatting.

*Solution*: Switched to the official Yutori Python SDK which handles authentication automatically and provides better error handling.

**3. Voice Interaction State Management**

The system would sometimes listen to its own voice output, creating infinite loops where the speech synthesis would trigger speech recognition.

*Solution*: Implemented a state machine with three distinct states (idle, listening, speaking) and carefully orchestrated pauses in speech recognition during synthesis output.

**4. Session Persistence**

When users directly accessed the dashboard without going through the search flow, the application would crash with `NoneType` errors because session data was empty.

*Solution*: Added fallback logic to load from saved files in the `/extractions` folder, enabling the dashboard to work even without active session data.

**5. Cost Optimization**

Initial implementation used paid API tiers which wouldn't be sustainable for a demo or MVP.

*Solution*: Migrated to entirely free AI models:
- Groq's `llama-3.3-70b-versatile` (free tier with fast inference)
- Leveraged free tiers of all other services

**6. Port Conflicts**

Encountered "Address already in use" error on port 5000 due to macOS AirPlay Receiver.

*Solution*: Changed application to run on port 5004.

**7. Real-time Image Matching**

Needed to automatically display relevant images based on conversation context without explicit user commands.

*Solution*: Developed keyword matching algorithm that analyzes AI response content for room types (kitchen, bathroom, bedroom, living room) and automatically switches to corresponding images.

## Accomplishments that we're proud of

1. **Seamless Multi-AI Integration**: Successfully orchestrated five different AI services into a single coherent pipeline, handling authentication, rate limits, and error states gracefully

2. **Voice-First UX**: Created a truly hands-free experience where users never need to touch a keyboard or read text - everything is spoken and heard

3. **Robust Error Handling**: Built fallback mechanisms for session recovery, API failures, and edge cases that make the system resilient

4. **Smart Context Awareness**: The system intelligently matches conversation context to visual content without requiring explicit "show me" commands

5. **Performance Optimization**: Achieved real-time response times using Groq's fast inference despite complex multi-service architecture

6. **Zero-Cost Operation**: Engineered the entire system to run on free API tiers, making it sustainable and accessible

7. **Clean Minimalist Design**: Resisted feature creep and created an interface that's just a microphone and image - proving that less is more

8. **Production-Ready Code**: Proper gitignore, environment variable management, and security practices that protect API keys

## What we learned

**Technical Skills:**

- **Web Automation Limits**: Learned the hard boundaries of web scraping - WebGL and canvas-rendered content cannot be extracted using traditional DOM methods

- **AI Service Landscape**: Gained deep understanding of different AI service types:
  - Search (Tavily) vs Extraction (Yutori) vs Analysis (Reka) vs Conversation (Groq)
  - When to use specialized models vs general-purpose LLMs
  - Entity extraction (Pioneer/GLiNER-2) has different use cases than chat completion

- **Voice Interface Design**: Discovered the complexity of managing conversation state:
  - Need to prevent feedback loops
  - Importance of timing delays between state transitions
  - Visual feedback is still crucial even in voice-first apps

- **API Cost Management**: Learned to evaluate free tiers and optimize for cost efficiency without sacrificing performance

**System Design:**

- **Graceful Degradation**: Building fallback mechanisms is not optional - users will always access systems in unexpected ways

- **Separation of Concerns**: Clear separation between search, extraction, analysis, and presentation layers made the system maintainable

- **File-Based State**: Simple file persistence can be more reliable than complex session management for certain use cases

**Development Process:**

- **Pivot Fast**: When Matterport extraction proved impossible, pivoting quickly saved the project

- **Incremental Integration**: Adding one AI service at a time and testing thoroughly prevented debugging nightmares

- **User Feedback Loop**: Iterating based on real usage (like discovering the need for voice-only output) led to better UX

## What's next for AI Virtual Tour

**Immediate Enhancements:**

1. **Multi-Property Comparison**: Allow users to search multiple properties and compare them side-by-side through voice commands like "Compare this with The Hub on University"

2. **Personalized Recommendations**: Learn user preferences over time and proactively suggest properties matching their criteria

3. **Virtual Tour Integration**: While we can't extract Matterport images, we can embed and control virtual tour iframes through Yutori, providing guided voice tours

4. **Scheduling Integration**: Direct integration with property management systems to book tours - "Schedule a viewing for tomorrow at 2pm"

**Advanced Features:**

5. **Multi-Modal Input**: Add support for uploading property screenshots or URLs directly for instant analysis

6. **Neighborhood Insights**: Integrate with mapping APIs to provide walkability scores, nearby amenities, and commute time analysis

7. **Financial Planning**: Connect with loan calculators to provide rent-to-income ratio analysis and budget recommendations

8. **Roommate Matching**: Build a platform where multiple users can search together and vote on properties through voice

**Technical Improvements:**

9. **Response Caching**: Cache Yutori extractions to avoid re-scraping the same properties, improving response time and reducing API costs

10. **Streaming Responses**: Implement streaming for Groq responses so users hear answers as they're generated instead of waiting for completion

11. **Multi-Language Support**: Extend Web Speech API configuration to support Spanish, Mandarin, and other languages for international students

12. **Mobile Native App**: Build iOS/Android apps using native speech APIs for better performance and offline capability

**Scaling Considerations:**

13. **Database Integration**: Move from file-based storage to PostgreSQL for production scalability

14. **Background Processing**: Queue Yutori extraction jobs using Celery/Redis for better handling of multiple concurrent users

15. **CDN Image Hosting**: Store extracted property images in S3/Cloudflare for faster loading

**Business Model:**

16. **Property Management SaaS**: License the technology to property management companies for their own listings

17. **Lead Generation**: Partner with properties to provide qualified leads from users who engage deeply with listings

18. **Premium Features**: Offer advanced analytics and comparison tools as a paid tier while keeping basic search free

The future of apartment search is conversational, intelligent, and effortless. AI Virtual Tour is just the beginning.
