from mega import Mega
import os

M_TOKEN = os.getenv("M_TOKEN")
keys = M_TOKEN.split("_")
# Login to MEGA
mega = Mega()
m = mega.login(keys[0],keys[1])

# Upload output.json
file_path = 'output.json'
uploaded_file = m.upload(file_path)
print(f"✅ Uploaded to MEGA successfully")
