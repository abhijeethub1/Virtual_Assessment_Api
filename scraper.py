import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime

DISCOURSE_URL = "https://discourse.onlinedegree.iitm.ac.in"
COURSE_URL = "https://courses.onlinedegree.iitm.ac.in"

# Use your original cookies - they might need to be refreshed
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://discourse.onlinedegree.iitm.ac.in/latest",
    "X-Requested-With": "XMLHttpRequest",
    "Cookie": "_forum_session=YIW58jzutbklF7LYG8KTWX865If3EO6yxlUWlN%2BZTo3UJqtVUb1JNV0cGVy6lHpXinIyI0g%2B5%2Blgmsmg3cvCxiEU6RptEV5d8PT%2F3maygU4X7by3UlY92qSlxVCop%2Bd3R%2FFI2CYow0FwjFaiDIe%2BTQMEihhbQN1jeadJOAm44dlnt4MnPkn43VIqeVQiKkiK1NLHMUQ5unqz9jXOJ51jcPqp62SLeslgAO5CTct07R1FchEzxWq35ape4R85rQj0RzlK%2FdkFc5J4s%2BMX8exfCq%2BwvGgLNQ%3D%3D--lWlckxizJauuEbdm--6VUv5QTr%2BVyh1gBbPoFXtA%3D%3D; _t=JwRI7U19KLOaBgx2YTMAwdSFLnFIhdL%2FvUQ0TjIiV84oSo2fR9mswVEasqrPlFgtFKt%2Fw4bBrSh6hng1%2BUkCiF3DHaAd0asSNyKO0hJT7JA%2FoTC%2BhTR%2BRIzpXMu8FISjVALR5Akc%2BEqwgHyoJPdC6iUYurHuyiHvJ5moD2zXrTi4iKr4zmh47OS0819Drzfx56hLIo0uixmvTsQHXQ05ouoaeR6RtqUT8vLfd2HSlv8QdojGm8wyWhjQAfxr7oDX%2BXwBoW05dXWv1jGmdJdgMSX2rBs6Njqug8VMaGv7R5uIhYeyLCdTTv39LK0KpU6u--7Rln96fAnENwA3XI--Gp7pRARMQRf4WimZStQbFA%3D%3D"
}

def scrape_discourse_posts(start_date, end_date):
    """Scrape Discourse posts with working authentication"""
    posts = []
    page = 1
    start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())

    while True:
        url = f"{DISCOURSE_URL}/latest.json?page={page}"
        print(f"Scraping page {page}...")

        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            
            # If forbidden, try with fresh cookies
            if response.status_code == 403:
                print("Session expired, getting new cookies...")
                # Manually update cookies here from browser
                new_cookies = input("Paste fresh cookies from browser: ")
                HEADERS["Cookie"] = new_cookies
                response = requests.get(url, headers=HEADERS, timeout=10)
                
            response.raise_for_status()
            data = response.json()

            topics = data.get("topic_list", {}).get("topics", [])
            if not topics:
                break

            for topic in topics:
                created_at = datetime.strptime(topic['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()

                if created_at < start_ts:
                    return posts

                if start_ts <= created_at <= end_ts:
                    topic_url = f"{DISCOURSE_URL}/t/{topic['slug']}/{topic['id']}.json"
                    topic_resp = requests.get(topic_url, headers=HEADERS)
                    topic_data = topic_resp.json()

                    for post in topic_data['post_stream']['posts']:
                        posts.append({
                            'topic_title': topic['title'],
                            'content': post['cooked'],
                            'url': f"{DISCOURSE_URL}/t/{topic['slug']}/{topic['id']}/{post['post_number']}",
                            'created_at': post['created_at']
                        })

            page += 1
            time.sleep(2)  # Be polite

        except Exception as e:
            print(f"Error scraping page {page}: {e}")
            break

    return posts


def scrape_course_content():
    """Scrape IITM course content - placeholder implementation"""
    return {
        "modules": [
            {"title": "Week 1", "content": "Intro to Jupyter, Pandas basics"},
            {"title": "Week 2", "content": "Data visualization, Matplotlib"},
            {"title": "Week 3", "content": "Numpy arrays, basic ops"}
        ]
    }

def save_data():
    discourse_posts = scrape_discourse_posts("2025-01-01", "2025-04-14")
    course_content = scrape_course_content()

    data = {
        "discourse_posts": discourse_posts,
        "course_content": course_content,
        "last_updated": datetime.now().isoformat()
    }

    with open("data.json", "w", encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(discourse_posts)} discourse posts and course content to data.json")

if __name__ == "__main__":
    save_data()
