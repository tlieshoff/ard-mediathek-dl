import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from ard_mediathek_dl.logger import log_info, log_error, log_debug, log_warning

def extract_m3u8_url(page_url, debug=False):
    log_info(f"Fetching ARD page: {page_url}")
    try:
        res = requests.get(page_url, timeout=10)
        res.raise_for_status()
    except Exception as e:
        log_error(f"Failed to load page: {e}")
        return None

    soup = BeautifulSoup(res.text, "html.parser")
    for script in soup.find_all("script"):
        if script.string and ".m3u8" in script.string:
            match = re.search(r'(https://[^\"\']+\.m3u8)', script.string)
            if match:
                log_debug(f"Found .m3u8: {match.group(1)}", debug)
                return match.group(1)

    log_error("Could not find any .m3u8 link in page scripts.")
    return None

def list_variants(master_url):
    try:
        r = requests.get(master_url)
        r.raise_for_status()
        lines = r.text.splitlines()
        variants = []
        for i, line in enumerate(lines):
            if line.startswith("#EXT-X-STREAM-INF"):
                resolution = re.search(r'RESOLUTION=(\d+x\d+)', line)
                next_line = lines[i + 1] if i + 1 < len(lines) else ""
                if resolution:
                    full_url = urljoin(master_url, next_line.strip())
                    variants.append((resolution.group(1), full_url))
        return variants
    except Exception as e:
        log_error(f"Failed to load playlist: {e}")
        return []

def choose_variant(master_url, quality="best", debug=False):
    variants = list_variants(master_url)
    if not variants:
        log_warning("No variants found, using master playlist directly.")
        return master_url

    log_debug(f"Available variants: {variants}", debug)
    variants_sorted = sorted(variants, key=lambda v: int(v[0].split('x')[1]))

    if quality == "best":
        return variants_sorted[-1][1]
    elif quality == "worst":
        return variants_sorted[0][1]
    else:
        for res, uri in variants_sorted:
            if quality in res or quality == res.split('x')[1]:
                return uri
        log_warning(f"Requested quality '{quality}' not found, defaulting to best.")
        return variants_sorted[-1][1]

def interactive_variant_choice(variants):
    print("[INFO] Available stream variants:")
    for idx, (res, uri) in enumerate(variants, 1):
        print(f"{idx}) {res} => {uri}")
    choice = input("\nEnter stream number to select: ")
    try:
        selected = variants[int(choice) - 1]
        print(f"\n[✓] Selected Stream URL:\n{selected[1]}\n")
        return selected[1]
    except Exception:
        log_error("Invalid selection.")
        return None
