import os
import json
import re

# Configuration
BLOG_DIR = 'blogs'
BOOK_DIR = 'books'
OUTPUT_BLOGS = 'blog_index.json'
OUTPUT_BOOKS = 'books_index.json'  # Renamed from library_index

def parse_front_matter(content):
    meta = {}
    match = re.search(r'^---\s+(.*?)\s+---', content, re.DOTALL)
    if match:
        yaml_content = match.group(1)
        for line in yaml_content.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                value = value.strip()
                
                # NEW: Remove surrounding quotes if they exist
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                    
                meta[key.strip()] = value
    return meta

# --- PART 1: BLOGS ---
blog_posts = []
if os.path.exists(BLOG_DIR):
    for filename in os.listdir(BLOG_DIR):
        if filename.endswith('.md'):
            with open(os.path.join(BLOG_DIR, filename), 'r', encoding='utf-8') as f:
                meta = parse_front_matter(f.read())
                if 'title' in meta:
                    blog_posts.append({
                        'title': meta.get('title'),
                        'date': meta.get('date', ''),
                        'desc': meta.get('desc', ''),
                        'file': filename
                    })
    blog_posts.sort(key=lambda x: x['date'], reverse=True)

with open(OUTPUT_BLOGS, 'w', encoding='utf-8') as f:
    json.dump(blog_posts, f, indent=2)
print(f"Generated {OUTPUT_BLOGS}")

# --- PART 2: BOOKS (Renamed) ---
books = []

if os.path.exists(BOOK_DIR):
    for book_folder in os.listdir(BOOK_DIR):
        book_path = os.path.join(BOOK_DIR, book_folder)
        
        # Check if directory and has meta.json
        if os.path.isdir(book_path) and 'meta.json' in os.listdir(book_path):
            
            with open(os.path.join(book_path, 'meta.json'), 'r', encoding='utf-8') as mf:
                book_meta = json.load(mf)
            
            chapters = []
            for filename in os.listdir(book_path):
                if filename.endswith('.md'):
                    with open(os.path.join(book_path, filename), 'r', encoding='utf-8') as cf:
                        chapter_meta = parse_front_matter(cf.read())
                        if 'title' in chapter_meta:
                            chapters.append({
                                'title': chapter_meta.get('title'),
                                'desc': chapter_meta.get('desc', ''),
                                'order': int(chapter_meta.get('order', 999)),
                                'file': filename
                            })
            
            chapters.sort(key=lambda x: x['order'])
            
            books.append({
                'id': book_folder,
                'details': book_meta,
                'chapters': chapters
            })

with open(OUTPUT_BOOKS, 'w', encoding='utf-8') as f:
    json.dump(books, f, indent=2)
print(f"Generated {OUTPUT_BOOKS}")

