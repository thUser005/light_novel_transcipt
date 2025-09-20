import os
import time
import json
import subprocess
import telebot
import gdown
from gpt4all import GPT4All
from datetime import datetime, timedelta

# --- Config ---
drive_url = "https://drive.google.com/uc?id=1c2XOp78-KgIECyMWpvhKyDVj74KiFv5L"
input_file = "pages_text.json"
output_file = "output.json"
model_dir = "models"
os.makedirs(model_dir, exist_ok=True)
model_path = os.path.join(model_dir, "Meta-Llama-3-8B-Instruct.Q4_0.gguf")
max_runtime = timedelta(hours=5, minutes=30)  # 5h30min

# --- Step 1: Download model if not exists ---
if not os.path.exists(model_path):
    print("📥 Downloading Meta-Llama-3-8B-Instruct.Q4_0.gguf from Google Drive...")
    try:
        gdown.download(drive_url, model_path, quiet=False, fuzzy=True, resume=True)
    except Exception as e:
        print(f"⚠️ gdown failed: {e}")
        print("👉 Falling back to curl...")
        try:
            subprocess.run(["curl", "-L", drive_url, "-o", model_path], check=True)
            print("✅ Model downloaded with curl")
        except subprocess.CalledProcessError as ce:
            print(f"❌ curl failed: {ce}")
            exit(1)
else:
    print("✅ Model already exists locally")

# --- Step 2: Load GPT4All model ---
model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf", model_path=model_dir, device="cpu")
print("✅ Model loaded successfully")

# --- Step 3: Load pages_text.json ---
with open(input_file, "r", encoding="utf-8") as f:
    pages_text = json.load(f)

# if below line uncomment do not modify this or remove its for testing.
page_text = pages_text[:5]

# --- Step 4: Load prompt template from prompt.txt ---
base_prompt = ''
try:
    with open("prompt.txt", "r", encoding="utf-8") as pf:
        base_prompt = pf.read()
    print("✅ prompt.txt loaded successfully")
except FileNotFoundError:
    print("⚠️ prompt.txt not found. Using default fallback prompt.")
   
# --- Step 5: Generate transcripts ---
output_transcripts = []  # flat list for all pages
start_time = datetime.now()

for page_num, page_text in pages_text.items():
    try:
        # Stop if runtime exceeds max_runtime
        if datetime.now() - start_time > max_runtime:
            print("⏱ Max runtime exceeded. Stopping processing...")
            break

        print(f"🟢 Processing {page_num}...")
        # Replace placeholder {page_text} inside prompt
        prompt = base_prompt.replace("{page_text}", str(page_text))
        transcript = []

        with model.chat_session():
            for token in model.generate(prompt, max_tokens=1000, streaming=True):
                transcript.append(token)

        structured_page = []
        full_text = "".join(transcript).split("\n")
        for line in full_text:
            line = line.strip()
            if not line:
                continue
            if line.startswith("**Narrator:**"):
                structured_page.append({"Narrator": line.replace("**Narrator:**", "").strip()})
            elif ":" in line:
                char, speech = line.split(":", 1)
                structured_page.append({char.strip(): speech.strip()})
            else:
                structured_page.append({"Narrator": line})

        output_transcripts.extend(structured_page)
        print(f"✅ Transcript from {page_num} appended\n")
        time.sleep(1)

    except Exception as e:
        print(f"⚠️ Error processing {page_num}: {e}. Skipping to next page.")
        continue

# --- Step 6: Save output.json ---
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(output_transcripts, f, ensure_ascii=False, indent=2)

print("✅ Final structured transcript saved to output.json")

# --- Step 7: Send file to Telegram ---
CHAT_ID = os.getenv("C_ID")
BOT_TOKEN = os.getenv("TOKEN")

def send_file_to_telegram(file_name: str):
    bot = telebot.TeleBot(BOT_TOKEN)
    if not os.path.exists(file_name):
        print(f"❌ File {file_name} not found")
        return
    with open(file_name, "rb") as f:
        bot.send_document(CHAT_ID, f, caption=f"📂 File sent: {file_name}")
    print(f"✅ File '{file_name}' sent to Telegram successfully")

if os.path.exists(output_file):
    send_file_to_telegram(output_file)
