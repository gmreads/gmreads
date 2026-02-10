#!/usr/bin/env python3
"""
Fetch Instagram cover images for Hugo posts.
Usage: python3 scripts/fetch-instagram-covers.py
"""

import os
import re
import json
import time
import urllib.request
from pathlib import Path

CONTENT_DIR = Path("content/literature")
IMAGES_DIR = Path("static/images/instagram")

def extract_post_id(content):
    """Extract Instagram post ID from Hugo shortcode."""
    match = re.search(r'\{\{<\s*instagram\s+([A-Za-z0-9_-]+)\s*>\}\}', content)
    return match.group(1) if match else None

def fetch_instagram_image(post_id):
    """Fetch Instagram post thumbnail URL by scraping the page."""
    url = f"https://www.instagram.com/p/{post_id}/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')

        # Try to find og:image meta tag
        og_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        if og_match:
            return og_match.group(1).replace('&amp;', '&')

        # Try to find image in JSON data
        json_match = re.search(r'"display_url":"([^"]+)"', html)
        if json_match:
            return json_match.group(1).replace('\\u0026', '&')

    except Exception as e:
        print(f"    Error fetching {post_id}: {e}")

    return None

def download_image(url, filepath):
    """Download image from URL."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(filepath, 'wb') as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"    Download error: {e}")
        return False

def update_frontmatter(filepath, image_path):
    """Add cover image to post front matter."""
    with open(filepath, 'r') as f:
        content = f.read()

    if 'cover:' in content:
        print("    Cover already exists, skipping")
        return

    # Find the end of front matter and insert cover before it
    parts = content.split('---', 2)
    if len(parts) >= 3:
        frontmatter = parts[1]
        body = parts[2]

        cover_yaml = f'\ncover:\n    image: "{image_path}"\n    hidden: false'
        new_content = f'---{frontmatter}{cover_yaml}\n---{body}'

        with open(filepath, 'w') as f:
            f.write(new_content)
        print("    Updated front matter")

def main():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    print("Scanning posts for Instagram embeds...\n")

    for md_file in CONTENT_DIR.glob("*.md"):
        filename = md_file.stem

        with open(md_file, 'r') as f:
            content = f.read()

        post_id = extract_post_id(content)

        if not post_id:
            print(f"  Skipping {filename} (no Instagram embed)")
            continue

        image_path = IMAGES_DIR / f"{filename}.jpg"

        if image_path.exists():
            print(f"  Skipping {filename} (image exists)")
            continue

        print(f"  Processing {filename} (post: {post_id})...")

        # Fetch thumbnail URL
        thumbnail_url = fetch_instagram_image(post_id)

        if not thumbnail_url:
            print("    Could not find thumbnail URL")
            continue

        # Download image
        print("    Downloading thumbnail...")
        if download_image(thumbnail_url, image_path):
            print(f"    Saved to {image_path}")
            update_frontmatter(md_file, f"/images/instagram/{filename}.jpg")

        # Rate limit
        time.sleep(2)

    print("\nDone! Run 'hugo server -D' to preview.")

if __name__ == "__main__":
    main()
