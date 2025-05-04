import requests
from bs4 import BeautifulSoup
import re

DOMAIN = "https://sakurazaka46.com"

def scrape_images(url):
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': DOMAIN
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    images = []

    path_pattern = re.compile(
        r'^/files/14/diary/s46/.*\.(?:jpe?g|png|webp)$',
        re.IGNORECASE
    )

    for img in soup.select('img[src]'):
        src = img['src']
        if path_pattern.search(src):
            clean_src = requests.utils.unquote(src)
            if clean_src.startswith('/'):
                clean_src = DOMAIN + clean_src
            images.append(clean_src)

    return images

def get_blog_posts():
    api_url = f"{DOMAIN}/s/s46app/api/json/diary?cd=blog"
    response = requests.get(api_url)
    data = response.json()
    
    posts = []
    for blog in data['blog']:
        clean_url = blog['link'].replace("s46app/", "s46/").split('?')[0]
        
        posts.append({
            'post_id': int(blog['id']),
            'url': clean_url,
            'member': blog['creator'],
            'title': blog['title'],
            'date': blog['pubdate']
        })
    
    return sorted(posts, key=lambda x: x['post_id'], reverse=True)
