import requests
from bs4 import BeautifulSoup
from datetime import datetime
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
    r'^/(files|images)/14/(?!.*(app/|common/pages/app_guide/images|s46/img|artist/|prof/)).*\.(?:jpe?g)$',
    re.IGNORECASE
    )
    blog_prof_section = soup.select_one('div.blog-prof-r')
    excluded_images = []
    if blog_prof_section:
        excluded_images = blog_prof_section.select('img[src]')
    for img in soup.select('img[src]'):
        if img in excluded_images:
            continue
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
    # excluded_ids = {59972}
    # posts = [p for p in posts if p['post_id'] not in excluded_ids]

    def parse_date(d): return datetime.strptime(d['date'], "%Y/%m/%d %H:%M:%S")
    return sorted(posts, key=parse_date, reverse=True)