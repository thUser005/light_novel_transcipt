import json
import time
import os
import gdown
from gpt4all import GPT4All

# --- Step 1: Download model file from Google Drive ---
# Your Google Drive share link:
drive_url = "https://drive.google.com/uc?id=1c2XOp78-KgIECyMWpvhKyDVj74KiFv5L"

# Local save path
model_dir = "models"
os.makedirs(model_dir, exist_ok=True)
model_path = os.path.join(model_dir, "gpt4all-j-v1.3-groovy.bin")

# Download if not exists
if not os.path.exists(model_path):
    print("📥 Downloading model from Google Drive...")
    gdown.download(drive_url, model_path, quiet=True)
else:
    print("✅ Model already exists locally")

# --- Step 2: Load GPT4All model from downloaded path ---
model = GPT4All("gpt4all-j-v1.3-groovy.bin", model_path=model_dir)
print("✅ Model loaded successfully")

# --- Step 3: Load pages_text.json ---
with open("pages_text.json", "r", encoding="utf-8") as f:
    pages_text = json.load(f)

output_transcripts = {}

# --- Step 4: Generate transcripts ---
for page_num, page_text in pages_text.items():
    prompt = f"""
    You are given text from a novel page. Separate it into a transcript format:
    - Use **Narrator:** for third-person descriptions and background.
    - Use the character's name for dialogue lines.
    - Keep the order of events as in the text.
    - Do not invent new content; just restructure it.

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
with open("output.json", "w", encoding="utf-8") as f:
    json.dump(output_transcripts, f, ensure_ascii=False, indent=2)

print("✅ Final structured transcript saved to output.json")

