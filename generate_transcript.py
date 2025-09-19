import os, telebot, time, json, gdown
from gpt4all import GPT4All

# --- Step 1: Download model file from Google Drive ---
# Replace with your Google Drive file ID
drive_url = "https://drive.google.com/uc?id=1c2XOp78-KgIECyMWpvhKyDVj74KiFv5L"

input_file = "pages_text.json"
output_file = "output.json"

# Local save path
model_dir = "models"
os.makedirs(model_dir, exist_ok=True)
model_path = os.path.join(model_dir, "Meta-Llama-3-8B-Instruct.Q4_0.gguf")

import subprocess

# --- Step 1: Download model file if not exists ---
if not os.path.exists(model_path):
    print("📥 Downloading Meta-Llama-3-8B-Instruct.Q4_0.gguf from Google Drive...")

    try:
        # Try gdown first (with resume support)
        gdown.download(drive_url, model_path, quiet=False, fuzzy=True, resume=True)
    except Exception as e:
        print(f"⚠️ gdown failed: {e}")
        print("👉 Falling back to curl...")

        # Use curl as fallback
        curl_url = "https://drive.google.com/uc?id=1c2XOp78-KgIECyMWpvhKyDVj74KiFv5L"
        try:
            subprocess.run(
                ["curl", "-L", curl_url, "-o", model_path],
                check=True
            )
            print("✅ Model downloaded with curl")
        except subprocess.CalledProcessError as ce:
            print(f"❌ curl failed: {ce}")
            exit(1)
else:
    print("✅ Model already exists locally")

# --- Step 2: Load GPT4All model from downloaded path ---
model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf", model_path=model_dir, device="cpu")
print("✅ Model loaded successfully")

# --- Step 3: Load pages_text.json ---
with open(input_file, "r", encoding="utf-8") as f:
    pages_text = json.load(f)

# keep only first 5 items (adjust as needed)
pages_text = dict(list(pages_text.items())[:5])
output_transcripts = {}

# --- Step 4: Load prompt template from prompt.txt ---
with open("prompt.txt", "r", encoding="utf-8") as pf:
    base_prompt = pf.read()

# --- Step 5: Generate transcripts ---
for page_num, page_text in pages_text.items():
    # Replace placeholder with actual text
    prompt = base_prompt.replace("{page_text}", page_text)

    print(f"🟢 Generating transcript for {page_num}...")
    transcript = []

    with model.chat_session():
        for token in model.generate(prompt, max_tokens=1000, streaming=True):
            transcript.append(token)

    # Join model output
    full_output = "".join(transcript).strip()

    # Save raw model response as is (since it should already be JSON per prompt)
    try:
        parsed_json = json.loads(full_output)
        output_transcripts[page_num] = parsed_json.get(page_num, parsed_json)
    except json.JSONDecodeError:
        # Fallback: store raw output if JSON parsing fails
        output_transcripts[page_num] = {"raw_output": full_output}

    print(f"✅ {page_num} transcript generated\n")
    time.sleep(1)

# --- Step 6: Save output.json ---
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(output_transcripts, f, ensure_ascii=False, indent=2)

print("✅ Final structured transcript saved to output.json")

# --- Step 7: Send file to Telegram ---
CHAT_ID = os.getenv("C_ID")
BOT_TOKEN = os.getenv("TOKEN")

def send_file_to_telegram(file_name: str):
    """
    Send a file to a Telegram chat using bot token and chat ID.
    BOT_TOKEN and C_ID must be set as environment variables.
    """
    bot = telebot.TeleBot(BOT_TOKEN)

    if not os.path.exists(file_name):
        raise FileNotFoundError(f"❌ File {file_name} not found")

    with open(file_name, "rb") as f:
        bot.send_document(CHAT_ID, f, caption=f"📂 File sent: {file_name}")

    print(f"✅ File '{file_name}' sent to Telegram successfully")

if os.path.exists(output_file):
    send_file_to_telegram(output_file)
