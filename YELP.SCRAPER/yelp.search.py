import time
import random
import csv
import subprocess
from urllib.parse import unquote, urlparse, parse_qs
from DrissionPage import ChromiumPage, ChromiumOptions

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
CSV_FILE = "yelp_restaurants_nj2.csv"

# ==========================================
# 🛠️ HELPER FUNCTIONS
# ==========================================

def get_real_browser_connection():
    """Connects to the Chrome window opened by launcher.py"""
    co = ChromiumOptions()
    # Connect to existing Chrome on port 9222
    co.set_address("127.0.0.1:9222") 
    page = ChromiumPage(co)
    return page

def clean_url(raw_url):
    """Cleans Yelp tracking URLs."""
    if not raw_url: return "N/A"
    
    # Handle Ad Redirects
    if "adredir" in raw_url:
        try:
            parsed = urlparse(raw_url)
            query_params = parse_qs(parsed.query)
            if 'redirect_url' in query_params:
                real_url = query_params['redirect_url'][0]
                return unquote(real_url)
        except:
            pass
            
    # Handle relative links
    if raw_url.startswith("/"):
        return f"https://www.yelp.com{raw_url}"
        
    return raw_url

def load_existing_urls():
    """Reads the CSV and returns a set of already scraped URLs."""
    seen_urls = set()
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("URL"):
                    seen_urls.add(row["URL"])
    except FileNotFoundError:
        pass # File doesn't exist yet, that's fine
    return seen_urls

def save_csv(data, seen_set):
    """Saves a row to CSV only if URL is unique."""
    # Data structure: [Name, Rating, Reviews, URL]
    url = data[3]
    
    if url in seen_set:
        # print(f"⚠️ Duplicate skipped: {data[0]}")
        return False

    # Append to file
    file_exists = True
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f: pass
    except FileNotFoundError:
        file_exists = False

    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Name", "Rating", "Reviews", "URL"])
        writer.writerow(data)
    
    # Add to memory set so we don't add it again in this session
    seen_set.add(url)
    print(f"💾 Saved: {data[0]}")
    return True

def human_mouse_move(page):
    """Moves mouse in a curve."""
    x_offset = random.randint(-50, 50)
    y_offset = random.randint(-50, 50)
    page.actions.move(x_offset, y_offset, duration=random.uniform(0.1, 0.3))

def clean_input_via_js(page, selector, text):
    """Clears input and types humanly."""
    ele = page.ele(selector)
    if not ele: return

    # Clear
    ele.run_js("this.value = ''; this.dispatchEvent(new Event('input', { bubbles: true }));")
    time.sleep(0.5)

    # Click & Type
    ele.hover()
    human_mouse_move(page)
    ele.click()
    print(f"⌨️  Typing '{text}'...")
    for char in text:
        page.actions.type(char)
        time.sleep(random.uniform(0.04, 0.12))
    time.sleep(1)

def click_next_page(page):
    """Handles Next Page with patience."""
    print("🔎 Looking for 'Next Page'...")
    page.scroll.to_bottom()
    time.sleep(random.uniform(2, 4)) 

    # Try multiple selectors
    next_btn = page.ele('css:button[class*="pagination-button"][value="submit"]')
    if not next_btn:
        next_btn = page.ele('text:Next Page')

    if next_btn:
        next_btn.scroll.to_see()
        time.sleep(0.5)
        next_btn.hover()
        time.sleep(random.uniform(0.3, 0.8))
        human_mouse_move(page)
        
        print("🖱️ Clicking Next...")
        next_btn.click()
        
        print("⏳ Waiting for page load...")
        time.sleep(random.uniform(6, 10)) # Longer wait for safety
        return True
    
    print("⚠️ Next Page not found.")
    return False

# ==========================================
# 🚀 MAIN LOGIC
# ==========================================

def start_scraping():
    print("--- 🕵️ YELP REAL BROWSER SEARCH BOT ---")
    
    # 1. Connect to Real Chrome
    try:
        page = get_real_browser_connection()
        print("✅ Connected to Chrome (Port 9222)")
    except Exception as e:
        print("❌ Connection Failed! Did you run launcher.py?")
        print(f"Error: {e}")
        return

    # 2. Load Existing Data (Anti-Duplicate)
    seen_urls = load_existing_urls()
    print(f"📚 Loaded {len(seen_urls)} existing businesses from CSV.")

    try:
        # 3. LOAD HOME
        print("🌍 Loading Yelp...")
        page.get("https://www.yelp.com/")
        time.sleep(2)

        # Check for Manual Block
        if "You have been blocked" in page.html:
            print("🛑 BLOCKED! Please solve the captcha in the browser window manually.")
            input("Press Enter after solving...")

        # Human Warm-up
        print("👀 Warming up...")
        page.scroll.down(400)
        time.sleep(1)
        page.scroll.up(200)

        # 4. SEARCH
        clean_input_via_js(page, '#search_description', 'Restaurants')
        clean_input_via_js(page, '#search_location', 'New Jersey')

        print("🖱️ Clicking Search...")
        btn = page.ele('css:button[type="submit"]')
        btn.hover()
        human_mouse_move(page)
        btn.click()
        time.sleep(5) 

        # 5. PAGINATION LOOP
        page_num = 1
        while True:
            print(f"\n📄 Processing Page {page_num}...")
            
            # Check Blocks (Manual Solve)
            if "You have been blocked" in page.html or "captcha" in page.html:
                print("⚠️ Block/Captcha detected! Please solve manually in Chrome.")
                input("Press ENTER once page is loaded again...")

            # EXTRACT DATA
            page.scroll.down(500)
            time.sleep(1)
            
            # Use Generic Card Selector
            items = page.eles('css:div[data-testid="serp-ia-card"]')
            if not items:
                items = page.eles('css:ul[class*="list__"] > li')

            count = 0
            new_count = 0
            
            for item in items:
                try:
                    # A. GET NAME & URL
                    name_tag = item.ele('css:h3 a')
                    if not name_tag: continue
                    
                    name = name_tag.text
                    raw_link = name_tag.attr('href')
                    final_url = clean_url(raw_link)

                    # B. GET RATING & REVIEWS
                    rating = "N/A"
                    reviews = "N/A"
                    
                    rating_box = item.ele('css:div[data-traffic-crawl-id="SearchResultBizRating"]')
                    
                    if rating_box:
                        spans = rating_box.eles('tag:span')
                        if len(spans) >= 1:
                            rating = spans[0].text
                        if len(spans) >= 2:
                            reviews = spans[1].text
                    
                    # Print & Save (With Duplicate Check)
                    # We pass 'seen_urls' to check efficiently
                    saved = save_csv([name, rating, reviews, final_url], seen_urls)
                    
                    count += 1
                    if saved:
                        new_count += 1
                        print(f"   🏢 {name[:20]}... | ⭐ {rating} | 🗣️ {reviews}")
                    
                except Exception as e:
                    continue
            
            print(f"🎉 Processed {count} items ({new_count} new) on Page {page_num}.")

            # NEXT PAGE
            if not click_next_page(page):
                print("✅ End of Pages reached.")
                break
            
            page_num += 1
            # Real Browser Pause (Human behavior)
            time.sleep(random.uniform(5, 8)) 

    except Exception as e:
        print(f"💀 ERROR: {e}")

if __name__ == "__main__":
    start_scraping()