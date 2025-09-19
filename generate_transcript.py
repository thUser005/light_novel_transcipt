import os, telebot, time, json, gdown, subprocess, traceback
from gpt4all import GPT4All

# --- Config ---
drive_url = "https://drive.google.com/uc?id=1c2XOp78-KgIECyMWpvhKyDVj74KiFv5L"
input_file = "pages_text.json"
output_file = "output.json"
model_dir = "models"
os.makedirs(model_dir, exist_ok=True)
model_path = os.path.join(model_dir, "Meta-Llama-3-8B-Instruct.Q4_0.gguf")

# Max run time: 5 hours 30 minutes
MAX_RUN_SECONDS = 5 * 3600 + 30 * 60

# --- Timer start ---
start_time = time.time()


# --- Step 1: Download model file if not exists ---
if not os.path.exists(model_path):
    print("📥 Downloading Meta-Llama-3-8B-Instruct.Q4_0.gguf from Google Drive...")

    try:
        gdown.download(drive_url, model_path, quiet=False, fuzzy=True, resume=True)
    except Exception as e:
        print(f"⚠️ gdown failed: {e}")
        print("👉 Falling back to curl...")

        curl_url = drive_url
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


# --- Step 2: Load GPT4All model ---
model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf", model_path=model_dir, device="cpu")
print("✅ Model loaded successfully")


# --- Step 3: Load input file ---
with open(input_file, "r", encoding="utf-8") as f:
    pages_text = json.load(f)

output_transcripts = {}


# --- Step 4: Load prompt template ---
with open("prompt.txt", "r", encoding="utf-8") as pf:
    base_prompt = pf.read()


# --- Step 5: Generate transcripts ---
for page_num, page_text in pages_text.items():
    # Timeout check
    elapsed = time.time() - start_time
    if elapsed > MAX_RUN_SECONDS:
        print("⏰ Time limit (5h30m) reached. Stopping execution...")
        break

    try:
        # Replace placeholder with actual text
        prompt = base_prompt.replace("{page_text}", page_text)

        print(f"🟢 Generating transcript for {page_num}...")
        transcript = []

        with model.chat_session():
            for token in model.generate(prompt, max_tokens=1000, streaming=True):
                transcript.append(token)

        # Join model output
        full_output = "".join(transcript).strip()

        # Try parsing as JSON
        try:
            parsed_json = json.loads(full_output)
            output_transcripts[page_num] = parsed_json.get(page_num, parsed_json)
        except json.JSONDecodeError:
            output_transcripts[page_num] = {"raw_output": full_output}

        print(f"✅ {page_num} transcript generated\n")
        time.sleep(1)

    except Exception as e:
        print(f"❌ Error on {page_num}: {e}")
        traceback.print_exc()
        # Save failure marker but continue
        output_transcripts[page_num] = {"error": str(e)}


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
        raise FileNotFoundError(f"❌ File {file_name} not found")

    with open(file_name, "rb") as f:
        bot.send_document(CHAT_ID, f, caption=f"📂 File sent: {file_name}")

    print(f"✅ File '{file_name}' sent to Telegram successfully")


try:
    if os.path.exists(output_file):
        send_file_to_telegram(output_file)
except Exception as e:
    print(f"⚠️ Failed to send file to Telegram: {e}")
