# Save as launcher.py
import subprocess
import os

# Adjust this path if your Chrome is elsewhere
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
USER_DATA_DIR = r"C:\ChromeBotProfile"

def launch_human_chrome():
    if not os.path.exists(USER_DATA_DIR):
        os.makedirs(USER_DATA_DIR)
        
    print("🚀 Launching REAL Chrome...")
    cmd = [
        CHROME_PATH,
        "--remote-debugging-port=9222", # Critical for connection
        f"--user-data-dir={USER_DATA_DIR}",
        "--no-first-run",
        "--password-store=basic",
        "https://www.yelp.com"
    ]
    subprocess.Popen(cmd)
    print("\n✅ Chrome is open! DO NOT CLOSE IT.")

if __name__ == "__main__":
    launch_human_chrome()