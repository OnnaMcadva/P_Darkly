import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import sys

BASE_URL = "http://localhost:8080/.hidden/"
OUTPUT_FILE = "scrapped_data"
MAX_WORKERS = 20

visited = set()
visited_lock = threading.Lock()
output_lock = threading.Lock()
counter = 0
counter_lock = threading.Lock()


def save(url, text):
    with output_lock:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(text.strip() + "\n")


def increment_counter():
    global counter
    with counter_lock:
        counter += 1
        print(f"\r[*] Visited: {counter} dirs", end="", flush=True)


def get_links(url):
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        links = []
        for link in soup.find_all("a"):
            href = link.get("href")
            if not href or href == "../":
                continue
            links.append((href, urljoin(url, href)))
        return links
    except Exception as e:
        print(f"\n[!] Failed to fetch {url}: {e}")
        return []


def fetch_readme(url):
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return resp.text.strip()
    except Exception as e:
        print(f"\n[!] Failed to fetch README at {url}: {e}")
        return None


def crawl(url, executor, futures):
    with visited_lock:
        if url in visited:
            return
        visited.add(url)

    increment_counter()
    links = get_links(url)

    for href, full_url in links:
        if href == "README":
            future = executor.submit(fetch_readme, full_url)
            futures.append((future, full_url))
        else:
            crawl(full_url, executor, futures)


def main():
    open(OUTPUT_FILE, "w").close()  # clear output file
    print(f"[*] Starting crawl at {BASE_URL}")

    futures = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        crawl(BASE_URL, executor, futures)

        print(f"\n[*] Fetching {len(futures)} README files...")
        for i, (future, url) in enumerate(futures, 1):
            try:
                text = future.result()
                if text:
                    save(url, text)
            except Exception as e:
                print(f"\n[!] Error reading result from {url}: {e}")
            print(f"\r[*] READMEs fetched: {i}/{len(futures)}", end="", flush=True)

    print(f"\n[+] Done. Results saved to '{OUTPUT_FILE}'")
    print(f"[+] Total directories visited: {counter}")
    print(f"[+] Total READMEs collected: {len(futures)}")
    print("\n[*] Filtering flag...")

    decoys = {"Nope", "Tu", "Non"}
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        lines = set(f.read().splitlines())

    flags = [l for l in lines if l and l not in decoys]
    if flags:
        print("\n[!!!] FLAG FOUND:")
        for flag in flags:
            print(f"    {flag}")
    else:
        print("[!] No flag found after filtering.")


if __name__ == "__main__":
    main()


# https://github.com/danielmiessler/SecLists/blob/master/Passwords/Common-Credentials/10k-most-common.txt
