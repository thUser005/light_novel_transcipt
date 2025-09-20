import os
import time
import json
import subprocess
import telebot
import gdown
from gpt4all import GPT4All
from datetime import datetime, timedelta
import unicodedata
import re

# --- Config ---
drive_url = "https://drive.google.com/uc?id=1c2XOp78-KgIECyMWpvhKyDVj74KiFv5L"
input_file = "pages_text.json"
output_file = "summary_output.txt"
model_dir = "models"
os.makedirs(model_dir, exist_ok=True)
model_path = os.path.join(model_dir, "Meta-Llama-3-8B-Instruct.Q4_0.gguf")
max_runtime = timedelta(minutes=50)  # 50 minutes max

# --- Step 1: Download model if not exists ---
if not os.path.exists(model_path):
    print("📥 Downloading model from Google Drive...")
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

# --- Sanitization ---
def sanitize_text(text):
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

for page_num in pages_text:
    pages_text[page_num] = sanitize_text(pages_text[page_num])

print("✅ pages_text.json loaded and sanitized successfully")

# --- Step 4: Load prompt template from prompt.txt ---
try:
    with open("prompt.txt", "r", encoding="utf-8") as pf:
        base_prompt = pf.read()
    print("✅ prompt.txt loaded successfully")
except FileNotFoundError:
    print("❌ prompt.txt not found. Please provide prompt.txt with the summary instruction.")
    exit(1)

# --- Utility: chunk pages into ~3000 token batches (approx by words) ---
def chunk_pages(pages, max_words=2500):
    chunks, current_chunk, word_count = [], [], 0
    for page_num, text in pages.items():
        words = text.split()
        if word_count + len(words) > max_words and current_chunk:
            chunks.append(current_chunk)
            current_chunk, word_count = [], 0
        current_chunk.append((page_num, text))
        word_count += len(words)
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

page_chunks = chunk_pages(pages_text, max_words=2500)
print(f"📖 Split into {len(page_chunks)} chunks for processing")

# --- Step 5: Generate summaries with conversation history ---
start_time = datetime.now()
conversation_history = ""  # preserve across chunks

for i, chunk in enumerate(page_chunks, 1):
    try:
        if datetime.now() - start_time > max_runtime:
            print("⏱ Max runtime exceeded. Stopping processing...")
            break

        print(f"🟢 Processing chunk {i}/{len(page_chunks)}...")

        # Combine all pages in this chunk into one text block
        combined_text = "\n".join([f"{p[0]}: {p[1]}" for p in chunk])

        # Build prompt with conversation history
        prompt = conversation_history + "\n\n" + base_prompt.replace("{page_text}", combined_text)

        summary_tokens = []
        with model.chat_session():
            for token in model.generate(prompt, max_tokens=1200, streaming=True):
                summary_tokens.append(token)

        summary_text = "".join(summary_tokens).strip()

        # Append new summary to conversation history
        conversation_history += f"\n\n--- Chunk {i} Summary ---\n{summary_text}"

        # Save incrementally to text file
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"--- Chunk {i} Summary ---\n")
            f.write(summary_text + "\n\n")

        print(f"✅ Chunk {i} summary saved\n")
        time.sleep(1)

    except Exception as e:
        print(f"⚠️ Error processing chunk {i}: {e}. Skipping.")
        continue

print(f"✅ All summaries saved in '{output_file}'")

# --- Optional: send summary file to Telegram ---
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
    pages_text = json.load(f)

# Keep first 5 pages for testing (adjust as needed)
pages_text = dict(list(pages_text.items())[:])

# --- Sanitization ---
def sanitize_text(text):
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

for page_num in pages_text:
    pages_text[page_num] = sanitize_text(pages_text[page_num])

print("✅ pages_text.json loaded and sanitized successfully")

# --- Step 4: Load prompt template from prompt.txt ---
try:
    with open("prompt.txt", "r", encoding="utf-8") as pf:
        base_prompt = pf.read()
    print("✅ prompt.txt loaded successfully")
except FileNotFoundError:
    print("❌ prompt.txt not found. Please provide prompt.txt with the summary instruction.")
    exit(1)

# --- Step 5: Generate summaries ---
start_time = datetime.now()

for page_num, page_text in pages_text.items():
    try:
        # Stop if runtime exceeds max_runtime
        if datetime.now() - start_time > max_runtime:
            print("⏱ Max runtime exceeded. Stopping processing...")
            break

        print(f"🟢 Summarizing {page_num}...")

        # Replace placeholder in prompt with actual page content
        prompt = base_prompt.replace("{page_text}", page_text)
        summary_tokens = []

        with model.chat_session():
            for token in model.generate(prompt, max_tokens=1000, streaming=True):
                summary_tokens.append(token)

        summary_text = "".join(summary_tokens).strip()

        # --- Step 6: Save summary to text file (append mode) ---
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"--- Summary of {page_num} ---\n")
            f.write(summary_text + "\n\n")

        print(f"✅ Summary for {page_num} saved\n")
        time.sleep(1)

    except Exception as e:
        print(f"⚠️ Error processing {page_num}: {e}. Skipping to next page.")
        continue

print(f"✅ All summaries saved in '{output_file}'")

# --- Optional: send summary file to Telegram ---
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


