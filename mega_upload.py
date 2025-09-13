import os
import telebot

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


send_file_to_telegram('t.py')