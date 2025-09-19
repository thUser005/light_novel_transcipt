import requests
import os
import json

# Replace with your bot token
BOT_TOKEN = '1810771437$8061823462:AAGqdn20vs4qDWhLYBJZ4LJP_fE6C4r7Mpo'

def get_updates():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    response = requests.get(url)
    
    if response.status_code != 200:
        print("❌ Error:", response.text)
        return
    
    data = response.json()
    print("🔎 Raw Response:\n", json.dumps(data, indent=2))
    
    # Try extracting chat_id
    try:
        chat_id = data["result"][-1]["message"]["chat"]["id"]
        print(f"\n✅ Your chat ID is: {chat_id}")
    except (KeyError, IndexError):
        print("\n⚠️ No messages found. Send a message to your bot first.")

if __name__ == "__main__":
    get_updates()
