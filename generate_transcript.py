
import os,telebot,time,json,gdown
from gpt4all import GPT4All

# --- Step 1: Download model file from Google Drive ---
# Replace with your Google Drive file ID
drive_url = "https://drive.google.com/uc?id=1c2XOp78-KgIECyMWpvhKyDVj74KiFv5L"

input_file = "pages_text.json"
output_file = 'output.json'

# Local save path
model_dir = "models"
os.makedirs(model_dir, exist_ok=True)
model_path = os.path.join(model_dir, "Meta-Llama-3-8B-Instruct.Q4_0.gguf")

# Download only if not exists
if not os.path.exists(model_path):
    print("📥 Downloading Meta-Llama-3-8B-Instruct.Q4_0.gguf from Google Drive...")
    gdown.download(drive_url, model_path, quiet=True)
else:
    print("✅ Model already exists locally")

# --- Step 2: Load GPT4All model from downloaded path ---
model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf", model_path=model_dir, device="cpu")
print("✅ Model loaded successfully")

# --- Step 3: Load pages_text.json ---
with open(input_file, "r", encoding="utf-8") as f:
    pages_text = json.load(f)
# keep first 20 items
pages_text = dict(list(pages_text.items())[:20])
output_transcripts = {}

# --- Step 4: Generate transcripts ---
for page_num, page_text in pages_text.items():
    prompt = f"""
You are given text from a novel page. Separate it into a transcript format:

- Use **Narrator:** for third-person descriptions and background.
- Use the character's name for dialogue lines.
- Keep the order of events as in the text.
- Do not invent new content; just restructure it.
- For each line, also provide:
  - "tone": The most likely emotional tone (angry, sad, happy, frustrated, neutral, etc.).
  - "confidence": A number from 1–10 showing how confident you are about the tone classification.

Return the output strictly in JSON format like this:

{{
  "page_X": [
    {{
      "Narrator": {{
        "text": "...",
        "tone": "...",
        "confidence": "rating should be in between 1 to 10"
      }}
    }},
    {{
      "CharacterName": {{
        "text": "...",
        "tone": "...",
        "confidence": "rating should be in between 1 to 10"
      }}
    }}
  ]
}}

Text:
{page_text}
"""

    print(f"🟢 Generating transcript for {page_num}...")
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
            structured_page.append({"Unknown": line})

    output_transcripts[page_num] = structured_page
    print(f"\n✅ {page_num} transcript generated\n")
    time.sleep(1)

# --- Step 5: Save output.json ---
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(output_transcripts, f, ensure_ascii=False, indent=2)

print("✅ Final structured transcript saved to output.json")


CHAT_ID = os.getenv("C_ID")
BOT_TOKEN = os.getenv('TOKEN')

def send_file_to_telegram(file_name: str):
    """
    Send a file to a Telegram chat using bot token and chat ID
    stored in the environment variable T_TOKEN.
    
    Format of T_TOKEN should be: BOT_TOKEN_CHATID
    Example: "1234567890:ABCDEFghIJKLmnoPQRstuVWxyZ_-1001234567890"
    """
    # T_TOKEN = os.getenv("T_TOKEN")
    # if not T_TOKEN:
    #     raise ValueError("❌ Environment variable T_TOKEN not set")


    bot = telebot.TeleBot(BOT_TOKEN)

    if not os.path.exists(file_name):
        raise FileNotFoundError(f"❌ File {file_name} not found")

    with open(file_name, "rb") as f:
        bot.send_document(CHAT_ID, f, caption=f"📂 File sent: {file_name}")

    print(f"✅ File '{file_name}' sent to Telegram successfully")



if os.path.exists(output_file):
    send_file_to_telegram(output_file)




if os.path.exists(output_file):
    send_file_to_telegram(output_file)

