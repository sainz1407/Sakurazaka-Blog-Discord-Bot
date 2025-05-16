import requests
from bs4 import BeautifulSoup
from datetime import datetime

DOMAIN = "https://sakurazaka46.com"

def scrape_images(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    images = []
    seen = set()
    for img in soup.select('img[src]'):
        src = img['src']
        if src.startswith('/'):
            src = DOMAIN + src
        src = requests.utils.unquote(src)
        if src not in seen:
            seen.add(src)
            images.append(src)
    return images

def get_blog_posts():
    api_url = f"{DOMAIN}/s/s46app/api/json/diary?cd=blog&get=B"
    headers = {'Accept-Encoding': 'gzip, deflate', 'User-Agent': 'Mozilla/5.0'}
    params = {
        'getnum': '3',  # Limit new post
        'st': '0'
    }
    response = requests.get(api_url, headers=headers, params=params)
    data = response.json()
    
    posts = []
    for blog in data['blog']:
        clean_url = blog['link'].replace("s46app/", "s46/").split('?')[0]
        
        html_content = blog.get('content', '')
        post_images = []
        if '<img' in html_content:
            post_images = scrape_images(html_content)

        posts.append({
            'post_id': int(blog['id']),
            'url': clean_url,
            'member': blog['creator'],
            'title': blog['title'],
            'date': blog['pubdate'],
            'images': post_images
        })
    # excluded_ids = {59972}
    # posts = [p for p in posts if p['post_id'] not in excluded_ids]

    def parse_date(d): return datetime.strptime(d['date'], "%Y/%m/%d %H:%M:%S")
    return sorted(posts, key=parse_date, reverse=True)
