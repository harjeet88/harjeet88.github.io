import os
import json
import re
from datetime import datetime

# Configuration
BLOG_DIR = 'blogs'
OUTPUT_FILE = 'blog_index.json'

def parse_front_matter(content):
    """Extracts metadata from the YAML front matter between --- lines."""
    meta = {}
    # Regex to find content between the first two ---
    match = re.search(r'^---\s+(.*?)\s+---', content, re.DOTALL)
    if match:
        yaml_content = match.group(1)
        for line in yaml_content.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                meta[key.strip()] = value.strip()
    return meta

posts = []

# Scan the blogs directory
if not os.path.exists(BLOG_DIR):
    os.makedirs(BLOG_DIR)

for filename in os.listdir(BLOG_DIR):
    if filename.endswith('.md'):
        filepath = os.path.join(BLOG_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            meta = parse_front_matter(content)
            
            # Only add if we found a title
            if 'title' in meta:
                posts.append({
                    'title': meta.get('title'),
                    'date': meta.get('date'),
                    'desc': meta.get('desc', ''),
                    'file': filename
                })

# Sort posts by date (newest first)
posts.sort(key=lambda x: x['date'], reverse=True)

# Save to JSON
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(posts, f, indent=2)

print(f"Successfully generated index for {len(posts)} posts.")
