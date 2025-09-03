# import os, re, time, json, hashlib, pathlib, requests
# from urllib.parse import quote_plus
# from bs4 import BeautifulSoup

# DATA_DIR = os.getenv("DATA_DIR", "data")
# CACHE_DIR = os.path.join(DATA_DIR, "policies")
# URL_CACHE_FILE = os.path.join(CACHE_DIR, "url_cache.json")
# os.makedirs(CACHE_DIR, exist_ok=True)

# HEADERS = {
#     "User-Agent": "Mozilla/5.0 (+https://healthbridge.internal)",
#     "Accept": "text/html,application/pdf;q=0.9,*/*;q=0.8",
# }

# def _load_url_cache():
#     if os.path.exists(URL_CACHE_FILE):
#         with open(URL_CACHE_FILE, "r", encoding="utf-8") as f:
#             return json.load(f)
#     return {}

# def _save_url_cache(cache):
#     with open(URL_CACHE_FILE, "w", encoding="utf-8") as f:
#         json.dump(cache, f, ensure_ascii=False, indent=2)

# def duckduckgo_pdf_search(query, max_results=8):
#     # Simple HTML search (no API) – respects rate limits.
#     # NOTE: If DDG throttles, add sleeps/backoff or swap to a paid API.
#     url = f"https://duckduckgo.com/html/?q={quote_plus(query)}+filetype%3Apdf"
#     resp = requests.get(url, headers=HEADERS, timeout=30)
#     resp.raise_for_status()
#     soup = BeautifulSoup(resp.text, "html.parser")
#     links = []
#     for a in soup.select("a.result__a"):
#         href = a.get("href")
#         if href and href.lower().endswith(".pdf"):
#             links.append(href)
#         if len(links) >= max_results:
#             break
#     return links

# def _insurer_key(name: str) -> str:
#     return re.sub(r"[^a-z0-9]+", "-", (name or "unknown").strip().lower())

# def _filehash(text: str) -> str:
#     return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

# def download_and_cache_pdf(url: str, insurer: str) -> str:
#     insurer_folder = os.path.join(CACHE_DIR, _insurer_key(insurer))
#     os.makedirs(insurer_folder, exist_ok=True)
#     fname = _filehash(url) + ".pdf"
#     fpath = os.path.join(insurer_folder, fname)
#     if os.path.exists(fpath):
#         return fpath
#     r = requests.get(url, headers=HEADERS, timeout=60)
#     r.raise_for_status()
#     with open(fpath, "wb") as f:
#         f.write(r.content)
#     return fpath

# def find_or_fetch_policy_pdf(insurer_name: str, keywords: list[str] = None) -> str | None:
#     """
#     1) Check local cache of discovered URLs for insurer.
#     2) If not found, search DDG for '{insurer} health insurance policy pdf {keywords}'.
#     3) Download first working PDF to local cache and return its local path.
#     """
#     if not insurer_name:
#         insurer_name = "unknown"
#     url_cache = _load_url_cache()
#     key = _insurer_key(insurer_name)
#     insurer_cache = url_cache.get(key, [])

#     # Prefer cached URLs
#     for url in insurer_cache:
#         try:
#             return download_and_cache_pdf(url, insurer_name)
#         except Exception:
#             continue

#     # Fresh search
#     kw = " ".join(keywords or [])
#     query = f"{insurer_name} health insurance policy pdf {kw}".strip()
#     try:
#         urls = duckduckgo_pdf_search(query)
#     except Exception:
#         urls = []

#     ok_urls = []
#     for url in urls:
#         try:
#             path = download_and_cache_pdf(url, insurer_name)
#             ok_urls.append(url)
#             # Save the first successful and return
#             url_cache[key] = list(dict.fromkeys(insurer_cache + ok_urls))[:10]
#             _save_url_cache(url_cache)
#             return path
#         except Exception:
#             time.sleep(1)
#             continue

#     # If nothing worked, remember attempted URLs to avoid repeats
#     if urls:
#         url_cache[key] = list(dict.fromkeys(insurer_cache + urls))[:10]
#         _save_url_cache(url_cache)
#     return None

import os, re, time, json, hashlib, requests, pathlib
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

try:
    from duckduckgo_search import DDGS
    DUCK_API = True
except ImportError:
    DUCK_API = False

DATA_DIR = os.getenv("DATA_DIR", "data")
CACHE_DIR = os.path.join(DATA_DIR, "policies")
URL_CACHE_FILE = os.path.join(CACHE_DIR, "url_cache.json")
os.makedirs(CACHE_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (+https://healthbridge.internal)",
    "Accept": "text/html,application/pdf;q=0.9,*/*;q=0.8",
}

def _load_url_cache():
    if os.path.exists(URL_CACHE_FILE):
        with open(URL_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def _save_url_cache(cache):
    with open(URL_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def _insurer_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (name or "unknown").strip().lower())

def _filehash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

def download_and_cache_pdf(url: str, insurer: str) -> str:
    insurer_folder = os.path.join(CACHE_DIR, _insurer_key(insurer))
    os.makedirs(insurer_folder, exist_ok=True)
    fname = _filehash(url) + ".pdf"
    fpath = os.path.join(insurer_folder, fname)
    if os.path.exists(fpath):
        return fpath
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    with open(fpath, "wb") as f:
        f.write(r.content)
    return fpath

def duckduckgo_pdf_search_html(query, max_results=8):
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}+filetype%3Apdf"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.select("a.result__a"):
        href = a.get("href")
        if href and href.lower().endswith(".pdf"):
            links.append(href)
        if len(links) >= max_results:
            break
    return links

def duckduckgo_pdf_search_api(query, max_results=8):
    results = []
    if not DUCK_API:
        return []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            url = r.get("href")
            if url and url.lower().endswith(".pdf"):
                results.append(url)
    return results

def find_or_fetch_policy_pdf(insurer_name: str, keywords=None) -> str | None:
    if not insurer_name:
        return None

    key = _insurer_key(insurer_name)
    insurer_folder = os.path.join(CACHE_DIR, key)
    os.makedirs(insurer_folder, exist_ok=True)

    # Manual PDF fallback
    manual_path = os.path.join(insurer_folder, "manual.pdf")
    if os.path.exists(manual_path):
        return manual_path

    # Try cached URLs
    url_cache = _load_url_cache()
    for url in url_cache.get(key, []):
        try:
            return download_and_cache_pdf(url, insurer_name)
        except Exception:
            continue

    # Search online
    query = f"{insurer_name} health insurance policy pdf {' '.join(keywords or [])}"
    urls = duckduckgo_pdf_search_api(query)
    if not urls:
        urls = duckduckgo_pdf_search_html(query)

    ok_urls = []
    for url in urls:
        try:
            pdf_path = download_and_cache_pdf(url, insurer_name)
            ok_urls.append(url)
            url_cache[key] = list(dict.fromkeys(url_cache.get(key, []) + ok_urls))
            _save_url_cache(url_cache)
            return pdf_path
        except Exception:
            time.sleep(1)
            continue

    return None
