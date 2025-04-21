import re
from ard_mediathek_dl.utils import extract_clean_slug, extract_air_date_from_url

def test_extract_clean_slug_valid():
    url = "https://www.ardmediathek.de/video/serie-name/episode-title/ARD123"
    series, slug = extract_clean_slug(url)
    assert series == "serie-name"
    assert re.match(r"episode_title", slug)

def test_extract_clean_slug_fallback():
    url = "https://www.ardmediathek.de/video/"
    series, slug = extract_clean_slug(url)
    assert series == "unknown"
    assert slug.startswith("video_")

def test_extract_air_date_from_url_valid():
    url = "https://www.ardmediathek.de/video/sendung/2024-04-15/ARD123"
    date = extract_air_date_from_url(url)
    assert date == "2024-04-15"

def test_extract_air_date_from_url_fallback():
    url = "https://www.ardmediathek.de/video/sendung/ARD123"
    date = extract_air_date_from_url(url)
    assert re.match(r"\d{4}-\d{2}-\d{2}", date)
