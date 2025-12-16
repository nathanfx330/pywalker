"""
=====================================================
 PROJECT: PyWalker v1.5 (Hotfix)
=====================================================
 FIXES:
 1. Fixed 'NoneType object is not callable' crash by
    using soup.new_tag() instead of element.new_tag().
 =====================================================
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3
from bs4 import BeautifulSoup
import time
import os
import re
import json
import random
import html
from urllib.parse import urljoin

# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# [SETTINGS]
# ==========================================
RECIPE_FILE = "pywalker_recipes.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

CSS = """
<style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #eef2f5; color: #333; }
    .thread-header { background: #fff; padding: 25px; border-left: 6px solid #2980b9; margin-bottom: 25px; border-radius: 4px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .thread-title { margin: 0 0 10px 0; font-size: 1.8em; color: #2c3e50; }
    .source-link { font-size: 0.9em; color: #666; background: #f8f9fa; padding: 10px; border: 1px solid #e9ecef; border-radius: 4px; display: inline-block; }
    .source-link a { color: #2980b9; text-decoration: none; word-break: break-all; font-weight: bold; }
    
    .post { background: #fff; padding: 20px; margin-bottom: 20px; border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .meta { color: #888; font-size: 0.85em; margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 8px; display: flex; justify-content: space-between; }
    .author { font-weight: bold; color: #2980b9; font-size: 1.1em; }
    
    .content { line-height: 1.6; font-size: 15px; overflow-wrap: break-word; }
    .content img { max-width: 100%; height: auto; display: block; margin: 10px 0; }
    .content blockquote { background: #f9f9f9; border-left: 4px solid #ccc; margin: 10px 0; padding: 10px; font-size: 0.95em; color: #555; }
    
    /* Injected Archive Link Style */
    .arclink { font-size: 0.75em; color: #d35400; text-decoration: none; margin-left: 4px; opacity: 0.8; }
    .arclink:hover { text-decoration: underline; opacity: 1; }

    .footer-nav { margin-top: 40px; padding: 20px; background: #fff; text-align: center; border-radius: 4px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .footer-nav a { display: inline-block; padding: 10px 25px; margin: 0 5px; background: #ecf0f1; text-decoration: none; color: #333; font-weight: bold; border-radius: 20px; transition: background 0.2s; }
    .footer-nav a:hover { background: #bdc3c7; }
    .footer-nav a.next { background: #2980b9; color: #fff; }
</style>
"""

# ==========================================
# [CONNECTION SETUP]
# ==========================================

def create_robust_session():
    session = requests.Session()
    retry = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(HEADERS)
    return session

session = create_robust_session()

# ==========================================
# [FILE OPS & HELPERS]
# ==========================================

def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}
    return {}

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)

def load_recipes(): return load_json(RECIPE_FILE)

def save_recipe(name, url, pattern, batch, split):
    data = load_recipes()
    data[name] = {"root_url": url, "pattern": pattern, "batch_size": int(batch), "split_limit": int(split)}
    data["_LATEST_"] = name
    save_json(RECIPE_FILE, data)

def get_part_filename(base_filename, part_num):
    name, ext = os.path.splitext(base_filename)
    return f"{name}_p{part_num}{ext}"

def clean_filename(title):
    clean = re.sub(r'[^a-zA-Z0-9]', '_', title)
    clean = re.sub(r'_{2,}', '_', clean)
    return clean[:50] + ".html"

# ==========================================
# [OUTPUT FLUSHER]
# ==========================================

def flush_buffer_to_file(filename, posts_buffer, folder, url_start, current_part, base_name, has_next):
    if not posts_buffer: return
    
    path = os.path.join(folder, filename)
    print(f"      [SAVE] Writing {len(posts_buffer)} posts to '{filename}'...")
    
    safe_url = html.escape(url_start)

    try:
        with open(path, 'w', encoding="utf-8") as f:
            f.write(f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{base_name} - Part {current_part}</title>{CSS}</head><body>")
            f.write('<div class="thread-header">')
            f.write(f'<h1 class="thread-title">{base_name} (Part {current_part})</h1>')
            f.write('<div class="source-link">')
            f.write(f'<strong>Start URL:</strong> <a href="{safe_url}" target="_blank">{safe_url}</a>')
            f.write('</div>')
            f.write('</div>')
            
            for p in posts_buffer:
                f.write(f"""<div class="post">
                    <div class="meta"><span class="author">{p['author']}</span> <span>Page {p['page_num']}</span></div>
                    <div class="content">{p['content']}</div>
                </div>""")
                
            f.write('<div class="footer-nav">')
            if current_part > 1:
                prev = get_part_filename(base_name, current_part - 1)
                f.write(f'<a href="{prev}">« Previous</a>')
            
            f.write(f'<span>&nbsp; Part {current_part} &nbsp;</span>')

            if has_next:
                next_f = get_part_filename(base_name, current_part + 1)
                f.write(f'<a href="{next_f}" class="next">Next Part »</a>')
                
            f.write('</div></body></html>')
    except Exception as e:
        print(f"   [ERR] Failed to write file: {e}")

# ==========================================
# [CORE LOGIC]
# ==========================================

def get_soup(url):
    attempts = 0
    max_attempts = 3
    while attempts < max_attempts:
        try:
            time.sleep(random.uniform(1.5, 3.5))
            r = session.get(url, timeout=45, verify=True)
            if r.status_code == 200:
                return BeautifulSoup(r.text, 'html.parser')
            elif r.status_code == 404:
                print(f"   [404] Page not found: {url}")
                return None
            else:
                print(f"   [ERR] HTTP {r.status_code}. Retrying...")
        except requests.exceptions.SSLError:
            try:
                r = session.get(url, timeout=45, verify=False)
                if r.status_code == 200: return BeautifulSoup(r.text, 'html.parser')
            except: pass
        except Exception as e:
            print(f"   [ERR] Network error: {e}")
            time.sleep(5)
        attempts += 1
        time.sleep(2)
    return None

def inject_archive_links(soup, soup_element):
    """
    Scans the post content for <a> tags.
    Injects a small (Archive) link next to them.
    """
    for a in soup_element.find_all('a', href=True):
        href = a['href']
        # Skip internal anchors, js, or existing wayback links
        if href.startswith('#') or href.startswith('javascript') or 'web.archive.org' in href:
            continue
            
        # Create the Archive link
        archive_url = f"https://web.archive.org/web/*/{href}"
        
        # Create new <a> tag using the main SOUP object (Safe method)
        new_tag = soup.new_tag("a", href=archive_url)
        new_tag.string = " (Archived)"
        new_tag['class'] = "arclink"
        new_tag['target'] = "_blank"
        
        # Insert after the original link
        a.insert_after(new_tag)
    
    return soup_element

def extract_posts(soup, page_num):
    posts = []
    # Try standard class names
    selectors = [
        {'class_': ['post', 'message', 'post_content', 'entry-content', 'comment-content']},
        {'id': re.compile(r'post_message_.*')},
    ]
    divs = []
    for sel in selectors:
        divs = soup.find_all(['div', 'td', 'article'], **sel)
        if divs: break
        
    # Fallback to old vBulletin styles
    if not divs: divs = soup.find_all('td', class_=['alt1'], id=re.compile(r'td_post_.*'))
    
    for d in divs:
        # 1. Cleanup junk
        for t in d(["script", "style", "form", "iframe", "noscript", "input", "button", "center"]): 
            t.decompose()
        
        # 2. Extract Author
        author = "Unknown"
        try:
            p = d.find_parent(['table', 'div', 'li', 'article'])
            if p:
                u = p.find(['a', 'span', 'b', 'strong'], class_=lambda x: x and ('user' in x.lower() or 'author' in x.lower() or 'name' in x.lower()))
                if u: author = u.get_text(strip=True)
        except: pass
        
        # 3. INJECT ARCHIVE LINKS (Pass 'soup' explicitly)
        d = inject_archive_links(soup, d)

        # 4. Save Content
        content = str(d).strip()
        if len(content) > 20:
            posts.append({'author': author, 'content': content, 'page_num': page_num})
    return posts

def find_next_page_link_original(soup, current_url, current_page_num):
    """
    Exactly the logic from your original V1 script.
    Calculates Target = Current + 1 and scans for that number.
    """
    if not soup: return None
    
    target = current_page_num + 1
    
    # 1. Exact Number Match (e.g. <a>2</a>)
    for a in soup.find_all('a', href=True):
        if a.get_text(strip=True) == str(target):
            return urljoin(current_url, a['href'])
    
    # 2. URL Patterns (e.g. page=2, page-2)
    target_patterns = [f"page={target}", f"page{target}", f"page-{target}", f"p={target}", f"start={target}"]
    for a in soup.find_all('a', href=True):
        href = a['href']
        for p in target_patterns:
            if p in href:
                return urljoin(current_url, href)

    # 3. "Next" Text Match
    for a in soup.find_all('a', href=True):
        txt = a.get_text(strip=True).lower()
        if "next" in txt or "›" in txt or ">" in txt:
            # Avoid "Last" or ">>"
            if "last" not in txt and ">>" not in txt:
                return urljoin(current_url, a['href'])

    return None

# ==========================================
# [RUNNER]
# ==========================================

def run_scraper(config_name, root_url, pattern, batch_size, split_limit, loop_mode=False):
    safe_config = clean_filename(config_name).replace('.html', '')
    output_dir = f"Archive_{safe_config}"
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    
    progress_file = f"{output_dir}/progress.json"
    progress_db = load_json(progress_file)
    
    print(f"\n--- JOB: {config_name} ---")
    print(f"Dir: {output_dir}")
    print(f"Goal: {batch_size} pages per thread per round.")
    
    print(f"\n[ROOT] Scanning: {root_url}")
    root_soup = get_soup(root_url)
    
    threads = []
    if root_soup:
        seen = set()
        for a in root_soup.find_all('a', href=True):
            href = a['href']
            if pattern in href:
                full = urljoin(root_url, href).split("#")[0]
                if re.search(r'page[=\-][0-9]{2,}', full): continue
                if "lastpost" in full or "do=newest" in full: continue
                
                if full not in seen:
                    seen.add(full)
                    title = a.get_text(strip=True)
                    if len(title) > 3:
                        threads.append({'title': title, 'url': full})

    print(f" -> Queued {len(threads)} threads.")
    if not threads: 
        print("[ERR] No threads matched your pattern. Check the URL and Pattern.")
        return

    round_counter = 1
    
    while True:
        incomplete_found = False
        print(f"\n=== ROUND {round_counter} START ===")

        for i, t in enumerate(threads):
            t_url = t['url']
            
            state = progress_db.get(t_url, {
                "title": t['title'],
                "base_filename": clean_filename(t['title']),
                "current_url": t_url,
                "total_pages": 0,
                "file_part": 1,
                "done": False
            })
            
            if state['done']: continue
            incomplete_found = True
            print(f"\n[{i+1}/{len(threads)}] {t['title'][:40]}...")
            
            posts_buffer = []
            pages_in_buffer = 0
            batch_count = 0
            
            buffer_start_url = state['current_url']
            
            while state['current_url']:
                # 1. BATCH CHECK
                if batch_size > 0 and batch_count >= batch_size:
                    if posts_buffer:
                        fname = get_part_filename(state['base_filename'], state['file_part'])
                        flush_buffer_to_file(fname, posts_buffer, output_dir, buffer_start_url, state['file_part'], state['base_filename'], True)
                        state['file_part'] += 1
                    
                    progress_db[t_url] = state
                    save_json(progress_file, progress_db)
                    print(f"   [PAUSE] Batch limit ({batch_size}) reached. Rotating...")
                    break 

                # 2. SCRAPE
                soup = get_soup(state['current_url'])
                if not soup:
                    print("   [ERR] Failed to load. Moving to next thread.")
                    break 
                
                current_page_number = state['total_pages'] + 1
                new_posts = extract_posts(soup, current_page_number)
                if new_posts: posts_buffer.extend(new_posts)
                
                print(f"   -> Page {current_page_number} ({len(new_posts)} posts)", end="\r")

                state['total_pages'] += 1
                pages_in_buffer += 1
                batch_count += 1
                
                # 3. GET NEXT URL (Original Logic)
                next_url = find_next_page_link_original(soup, state['current_url'], state['total_pages'])
                
                # 4. SPLIT CHECK
                if split_limit > 0 and pages_in_buffer >= split_limit:
                    has_more = True if next_url else False
                    fname = get_part_filename(state['base_filename'], state['file_part'])
                    
                    flush_buffer_to_file(fname, posts_buffer, output_dir, buffer_start_url, state['file_part'], state['base_filename'], has_more)
                    
                    posts_buffer = [] 
                    pages_in_buffer = 0
                    state['file_part'] += 1
                    
                    if next_url: buffer_start_url = next_url
                
                # 5. ADVANCE
                if next_url:
                    state['current_url'] = next_url
                else:
                    if posts_buffer:
                        fname = get_part_filename(state['base_filename'], state['file_part'])
                        flush_buffer_to_file(fname, posts_buffer, output_dir, buffer_start_url, state['file_part'], state['base_filename'], False)
                    
                    print(f"\n   [DONE] Thread Complete.")
                    state['current_url'] = None
                    state['done'] = True
                    progress_db[t_url] = state
                    save_json(progress_file, progress_db)
                    break 

                progress_db[t_url] = state
                save_json(progress_file, progress_db)

        if not incomplete_found:
            print("\n\n>>> JOB COMPLETE: All threads scraped. <<<")
            break
        
        if not loop_mode:
            print("\n--- SINGLE PASS COMPLETE ---")
            break
            
        print(f"\n--- Round {round_counter} Done. Cooldown 5s... ---")
        round_counter += 1
        time.sleep(5)

def menu():
    print("\n=== PyWalker v1.5 (Hotfix) ===")
    data = load_recipes()
    
    print("1. Single Pass")
    print("2. Loop Mode")
    loop_choice = input("Select Mode (1/2): ").strip()
    do_loop = True if loop_choice == '2' else False

    if data.get("_LATEST_"):
        last = data['_LATEST_']
        print(f"\n[1] Resume '{last}'")
        print(f"[2] Create New Profile")
        if input("Choice: ") == "1":
            c = data[last]
            run_scraper(last, c['root_url'], c['pattern'], c['batch_size'], c['split_limit'], loop_mode=do_loop)
            return

    print("\n--- NEW PROFILE ---")
    name = input("Profile Name: ")
    url = input("Root URL (Forum Index): ")
    pat = input("Link Pattern: ")
    try:
        batch = int(input("Batch Size (Rec: 10): "))
        split = int(input("Split Size (Rec: 50): "))
    except:
        batch = 10; split = 50
    
    save_recipe(name, url, pat, batch, split)
    run_scraper(name, url, pat, batch, split, loop_mode=do_loop)

if __name__ == "__main__":
    menu()