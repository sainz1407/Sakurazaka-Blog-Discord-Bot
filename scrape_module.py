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

def scrape_post_info(url):
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': DOMAIN
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    try:
        title = soup.select_one('div.inner.title-wrap h1.title').text.strip()
    except AttributeError:
        title = "Unknown Title"

    try:
        member = soup.select_one('div.blog-foot p.name').text.strip()
    except AttributeError:
        member = "Unknown Member"

    try:
        date = soup.select_one('div.blog-foot p.date').text.strip()
    except AttributeError:
        date = "Unknown Date"

    return member, title, date

def get_blog_posts(list_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': DOMAIN
    }
    response = requests.get(list_url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    posts = []
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        if "/s/s46/diary/detail/" in href:
            match = re.search(r'/diary/detail/(\d+)', href)
            if match:
                post_id = int(match.group(1))
                clean_url = DOMAIN + href.split('?')[0]
                posts.append({
                    'post_id': post_id,
                    'url': clean_url
                })

    unique = {p['post_id']: p for p in posts}
    sorted_posts = sorted(unique.values(), key=lambda x: x['post_id'])
    return sorted_posts