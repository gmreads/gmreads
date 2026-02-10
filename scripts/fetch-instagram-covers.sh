#!/bin/bash

# Fetch Instagram cover images for Hugo posts
# Usage: ./scripts/fetch-instagram-covers.sh

set -e

CONTENT_DIR="content/literature"
IMAGES_DIR="static/images/instagram"

# Create images directory
mkdir -p "$IMAGES_DIR"

echo "Scanning posts for Instagram embeds..."

# Find all markdown files with Instagram shortcodes
for file in "$CONTENT_DIR"/*.md; do
    [ -f "$file" ] || continue

    filename=$(basename "$file" .md)

    # Extract Instagram post ID from shortcode
    post_id=$(grep -oE '\{\{< instagram ([A-Za-z0-9_-]+) >\}\}' "$file" | sed -E 's/\{\{< instagram ([A-Za-z0-9_-]+) >\}\}/\1/' || true)

    if [ -z "$post_id" ]; then
        echo "  Skipping $filename (no Instagram embed)"
        continue
    fi

    image_path="$IMAGES_DIR/${filename}.jpg"

    # Skip if image already exists
    if [ -f "$image_path" ]; then
        echo "  Skipping $filename (image exists)"
        continue
    fi

    echo "  Processing $filename (post: $post_id)..."

    # Fetch oEmbed data
    oembed_url="https://api.instagram.com/oembed?url=https://www.instagram.com/p/${post_id}/"

    response=$(curl -s "$oembed_url" || echo "")

    if [ -z "$response" ]; then
        echo "    Failed to fetch oEmbed data"
        continue
    fi

    # Extract thumbnail URL
    thumbnail_url=$(echo "$response" | grep -oE '"thumbnail_url":"[^"]+' | cut -d'"' -f4 | sed 's/\\u0026/\&/g')

    if [ -z "$thumbnail_url" ]; then
        echo "    No thumbnail URL found"
        continue
    fi

    # Download image
    echo "    Downloading thumbnail..."
    if curl -s -o "$image_path" "$thumbnail_url"; then
        echo "    Saved to $image_path"

        # Update markdown file with cover image
        # Check if cover already exists in front matter
        if ! grep -q "^cover:" "$file"; then
            # Add cover after tags line
            sed -i '' "/^categories:/a\\
cover:\\
    image: \"/images/instagram/${filename}.jpg\"\\
    hidden: false
" "$file"
            echo "    Updated front matter"
        fi
    else
        echo "    Failed to download image"
    fi

    # Rate limit - be nice to Instagram
    sleep 1
done

echo ""
echo "Done! Run 'hugo server -D' to preview."
