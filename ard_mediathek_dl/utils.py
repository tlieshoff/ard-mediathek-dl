import re
from urllib.parse import urlparse
from datetime import datetime

def extract_clean_slug(url):
    parts = urlparse(url).path.split("/")
    try:
        series = parts[2].lower()
        slug = parts[3].lower().replace("-", "_")
        return series, slug
    except IndexError:
        return "unknown", f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def extract_air_date_from_url(url):
    match = re.search(r'(\d{4}-\d{2}-\d{2})', url)
    return match.group(1) if match else datetime.now().strftime("%Y-%m-%d")

def extract_subtitle_name(url):
    parts = urlparse(url).path.split("/")
    return parts[-1]
