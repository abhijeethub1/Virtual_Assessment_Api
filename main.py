from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
import json
import os
from groq import Groq
from fuzzywuzzy import fuzz
import re
import logging
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Load data
try:
    with open("data.json", "r", encoding='utf-8') as f:
        forum_data = json.load(f)
    logger.info(f"Loaded {len(forum_data)} forum topics")
except Exception as e:
    logger.error(f"Failed to load data: {e}")
    forum_data = []

class QuestionRequest(BaseModel):
    question: str
    image: Optional[str] = None

class Link(BaseModel):
    url: str
    text: str

class AnswerResponse(BaseModel):
    answer: str
    links: List[Link]

@app.get("/")
async def root():
    return {
        "message": "TDS Virtual TA API is running",
        "endpoints": {
            "ask_question": "POST /api/",
            "debug": "GET /debug_match",
            "docs": "GET /docs or /redoc"
        }
    }

def find_relevant_links(question: str) -> List[Link]:
    """Find matching forum topics with multiple matching strategies"""
    relevant = []
    if not forum_data or 'discourse_posts' not in forum_data:
        return relevant

    question_lower = question.lower()
    question_keywords = set(re.findall(r'\w+', question_lower))

    # Group posts by topic first
    topics = {}
    for post in forum_data['discourse_posts']:
        topic_title = post.get('topic_title', '').lower()
        if topic_title not in topics:
            topics[topic_title] = {
                'url': post['url'],
                'posts': []
            }
        topics[topic_title]['posts'].append(post)

    for topic_title, topic_data in topics.items():
        try:
            # Strategy 1: Title matching
            title_score = fuzz.partial_ratio(question_lower, topic_title)
            
            # Strategy 2: Content matching from all posts
            all_content = " ".join(p.get('content', '').lower() for p in topic_data['posts'])
            content_score = fuzz.partial_ratio(question_lower, all_content)
            
            # Strategy 3: Keyword matching
            content_keywords = set(re.findall(r'\w+', all_content))
            keyword_overlap = len(question_keywords & content_keywords)

            # Special case for GA5
            is_ga5_question = "ga5" in question_lower
            has_ga5_content = "ga5" in topic_title or "ga5" in all_content

            # Debug logging
            logger.debug(f"Checking topic: {topic_title[:50]}... | "
                        f"Title score: {title_score} | "
                        f"Content score: {content_score} | "
                        f"Keywords: {keyword_overlap} | "
                        f"GA5 match: {is_ga5_question and has_ga5_content}")

            # Matching criteria
            if (title_score > 75 or 
                content_score > 65 or 
                keyword_overlap >= 2 or
                (is_ga5_question and has_ga5_content)):
                
                # Find the most relevant post number
                best_post = None
                best_score = 0
                for post in topic_data['posts']:
                    post_score = fuzz.partial_ratio(question_lower, post.get('content', '').lower())
                    if post_score > best_score:
                        best_score = post_score
                        best_post = post

                link_text = topic_title[:100]  # Truncate if needed
                if best_post and best_score > 70:
                    # Extract post number from URL if available
                    post_num = best_post.get('url', '').split('/')[-1]
                    if post_num.isdigit():
                        link_text += f" (see post #{post_num})"
                
                relevant.append(Link(
                    url=topic_data['url'],
                    text=link_text
                ))

                if len(relevant) >= 3:
                    break

        except Exception as e:
            logger.error(f"Error processing topic: {e}")

    logger.info(f"Found {len(relevant)} relevant links for question")
    return relevant

@app.get("/debug_match")
async def debug_match():
    """Debug endpoint to test matching"""
    test_question = "Which AI model should I use for assignment GA5?"
    links = find_relevant_links(test_question)
    
    # Show matching scores for all topics
    matches = []
    for topic in forum_data:
        title = topic.get('title', '')
        score = fuzz.partial_ratio(test_question.lower(), title.lower())
        matches.append({
            "title": title,
            "score": score,
            "url": topic.get('url', '')
        })
    
    return {
        "test_question": test_question,
        "found_links": [dict(link) for link in links],
        "all_matches": sorted(matches, key=lambda x: -x['score'])
    }

@app.post("/api/", response_model=AnswerResponse)
async def answer_question(request: QuestionRequest):
    logger.info(f"\n{'='*50}\nNew question: {request.question}\n{'='*50}")
    
    # First find relevant links
    relevant_links = find_relevant_links(request.question)
    logger.info(f"Found links: {relevant_links}")

    # Generate answer
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    # Build system prompt that constrains the LLM
    system_prompt = f"""You are a Data Science Teaching Assistant for IIT Madras. Follow these rules:
1. Today's date is {datetime.now().strftime('%Y-%m-%d')}
2. Answer based ONLY on course content and forum discussions
3. NEVER invent URLs - only use provided links
4. When forum links exist, you MUST include them and reference them in your answer
5. For GA5 questions, specify to use gpt-3.5-turbo-0125
6. Always be helpful and supportive in your responses"""

    # Build user prompt with links if available
    user_prompt = request.question
    if relevant_links:
        user_prompt += "\n\nRelevant forum discussions:\n"
        user_prompt += "\n".join(f"- {link.text}: {link.url}" for link in relevant_links)
        user_prompt += "\n\nReference these links in your answer."

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama3-8b-8192",
            temperature=0.3,
            max_tokens=800
        )
        answer = response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        answer = "I encountered an error processing your question."
        if relevant_links:
            answer += "\n\nHowever, these forum discussions might help:\n"
            answer += "\n".join(f"- {link.text}: {link.url}" for link in relevant_links)

    logger.info(f"Answer: {answer[:200]}...")
    logger.info(f"Returning {len(relevant_links)} links")
    
    return AnswerResponse(
        answer=answer,
        links=relevant_links
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
