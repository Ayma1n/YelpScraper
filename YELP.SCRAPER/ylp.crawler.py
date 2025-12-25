import time
import random
import csv
from urllib.parse import unquote, urlparse, parse_qs
from DrissionPage import ChromiumPage, ChromiumOptions

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
INPUT_CSV = "yelp_restaurants_nj2.csv"
OUTPUT_CSV = "yelp_final_data.csv"

# ==========================================
# 🛠️ HELPER FUNCTIONS
# ==========================================

def get_real_browser_connection():
    """Connects to the Chrome window opened by launcher.py"""
    co = ChromiumOptions()
    # ⚠️ CRITICAL: Tell DrissionPage to connect to existing port 9222
    co.set_address("127.0.0.1:9222") 
    
    page = ChromiumPage(co)
    return page

def clean_website_link(raw_url):
    """Decodes Yelp's 'biz_redir'."""
    if not raw_url: return "N/A"
    try:
        if "biz_redir" in raw_url:
            parsed = urlparse(raw_url)
            query_params = parse_qs(parsed.query)
            if 'url' in query_params:
                return unquote(query_params['url'][0])
        return raw_url
    except:
        return raw_url

def save_csv(data):
    """Appends data to CSV."""
    headers = ["Name", "Phone", "Website", "Yelp URL"]
    write_header = False
    try:
        with open(OUTPUT_CSV, 'r', encoding='utf-8') as f: pass
    except FileNotFoundError:
        write_header = True

    with open(OUTPUT_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if write_header: writer.writerow(headers)
        writer.writerow(data)
    print(f"💾 Saved: {data[0]}")

# ==========================================
# 🚀 MAIN EXTRACTION LOGIC
# ==========================================

def process_url_human_mode(page, name, url):
    print(f"🌍 Navigating to: {name}...")
    page.get(url)
    
    # 1. HUMAN CHECK (Since we are using real chrome, blocks are rare)
    time.sleep(2)
    
    # If a block DOES happen, you can solve it manually because you can see the window!
    if "You have been blocked" in page.html or "captcha" in page.html:
        print("⚠️ BLOCK DETECTED!")
        print("🛑 Please solve the captcha manually in the Chrome window.")
        print("⌨️  Press ENTER here once you have solved it and see the page...")
        input() # Pauses script until you hit Enter

    # 2. INTERACT (Hours)
    hours_btn = page.ele('css:a[href="#location-and-hours"]')
    if hours_btn:
        hours_btn.scroll.to_see()
        time.sleep(random.uniform(0.5, 1.0))
        hours_btn.hover() 
    else:
        page.scroll.down(300)

    # 3. EXTRACT PHONE
    phone = "N/A"
    try:
        phone_label = page.ele('text:Phone number')
        if phone_label:
            phone_ele = phone_label.next()
            if phone_ele: phone = phone_ele.text
    except: pass

    # 4. EXTRACT WEBSITE
    website = "N/A"
    try:
        website_label = page.ele('text:Business website')
        if website_label:
            website_container = website_label.next()
            if website_container:
                website_link = website_container.ele('tag:a')
                if website_link:
                    raw_url = website_link.attr('href')
                    website = clean_website_link(raw_url)
    except: pass

    print(f"   📞 {phone} | 🌐 {website}")
    return phone, website

# ==========================================
# 🏁 CONTROLLER
# ==========================================

def start_real_browser_scraping():
    print("--- 🕵️ YELP 'REAL BROWSER' BOT ---")
    
    # 1. Connect to the browser you opened
    try:
        page = get_real_browser_connection()
        print("✅ Connected to Chrome on port 9222.")
    except Exception as e:
        print("❌ Could not connect! Did you run launcher.py?")
        print(f"Error: {e}")
        return

    # 2. Load URLs
    queue = []
    try:
        with open(INPUT_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("URL") and "http" in row.get("URL"):
                    queue.append((row["Name"], row["URL"]))
    except FileNotFoundError:
        print("❌ Input CSV not found!")
        return

    # 3. Process
    for name, url in queue:
        try:
            phone, website = process_url_human_mode(page, name, url)
            save_csv([name, phone, website, url])
            
            # Since this is a REAL browser, be gentle.
            # 6-10 seconds is safe.
            delay = random.uniform(6, 10)
            print(f"⏳ Human pause: {delay:.1f}s...")
            time.sleep(delay)
            
        except Exception as e:
            print(f"💀 Error on {name}: {e}")
            continue

if __name__ == "__main__":
    start_real_browser_scraping()