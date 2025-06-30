Here's the GitHub-formatted README.md without emojis and with the curl test example:

TDS Virtual Teaching Assistant
FastAPI Python Render

An AI-powered virtual teaching assistant for IIT Madras's Online Degree in Data Science program that automatically answers student questions based on course content and forum discussions.

Features
FastAPI backend with RESTful API endpoints
LLM-powered responses using Groq's LLaMA3 model
Smart forum search to find relevant discussion threads
Course-aware responses based on Tools in Data Science content
Quick response times (under 30 seconds)
CORS-enabled for web integration
API Endpoints
Main Endpoint
POST /api/ - Submit a student question and get an AI-generated response

Request format:

{
  "question": "Your question here",
  "image": null
}


Example response:
```json
{
  "answer": "The detailed answer to your question...",
  "links": [
    {
      "url": "https://discourse.example.com/t/relevant-topic",
      "text": "Relevant discussion topic"
    }
  ]
}
Testing with curl
You can test the API using curl commands:

curl -X POST "https://tds-virtual-ta-j53g.onrender.com/api/" \
  -H "Content-Type: application/json" \
  -d '{"question":"Which AI model should I use for GA5 assignment?"}'
Example response:

{
  "answer": "For the GA5 assignment, you must use gpt-3.5-turbo-0125 as specified in the course requirements. This ensures consistency in evaluation across all submissions.",
  "links": [
    {
      "url": "https://discourse.onlinedegree.iitm.ac.in/t/ga5-model-requirements/162241/4",
      "text": "GA5 model requirements (see post #4)"
    }
  ]
}
Other Endpoints
GET / - API status and documentation
GET /debug_match - Debug endpoint for testing question matching
Setup and Deployment
Prerequisites
Python 3.9 or later
Groq API key (set as GROQ_API_KEY environment variable)
Installation
Clone the repository:

git clone https://github.com/yourusername/tds-virtual-ta.git
cd tds-virtual-ta
Install dependencies:

pip install -r requirements.txt
Set up environment variables:

echo "GROQ_API_KEY=your_api_key_here" > .env
Running Locally
uvicorn main:app --reload
The API will be available at http://localhost:8000

Data Sources
The system uses two main data sources:

Course Content: Scraped from IITM's TDS course materials
Forum Discussions: From the IITM Discourse platform (Jan-Apr 2025)
To update the data:

python scraper.py
Project Structure
tds-virtual-ta/
├── main.py            # FastAPI application
├── scraper.py         # Data scraping script
├── data.json          # Course and forum data
├── requirements.txt   # Python dependencies
├── promptfoo.yaml     # Evaluation configuration
└── README.md          # This file
License
MIT License - See LICENSE for details.


This version:

1. Uses GitHub-flavored markdown for proper rendering
2. Includes a clear curl test example with both the command and expected response format
3. Maintains all technical details while being clean and professional
4. Uses minimal badges (only three) for key technologies
5. Has proper code blocks with syntax highlighting
6. Includes clear section headers for easy navigation

The formatting will render properly on GitHub and provides all necessary information for users to understand, test, and deploy the project.
