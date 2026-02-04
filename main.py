import asyncio
import logging
import re
from datetime import datetime
from collections import deque
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ================== SOZLAMALAR ==================
API_ID = 25573417
API_HASH = "b56082f4d86578c5a6948c7b964008f9"
SESSION_STRING = "1ApWapzMBu3fO0IyfsDsut6GvmfnTy98XJwUaItTW8tjLYkBIetG9iljXhUIx4oLEXwqTfMOw3HEQXQE9msN4W5rdJUAolpfEMUr2W0b1ES5o-505_2BKCc1OWSfw3zYG2rM9TBzDFEBTdAKyT5KzAFgU4hmXMrG68S8hhStMokh8Nh5bai5IkvgO1Wpqt5QKzwy0tTa4zK3BpijZ-5KgRqJJ_PdNsNfNzkT_VXcx6kj6WXQ8Q7v414bOTN7B9YISIN1xaK9cp5EbrvQzHExzE1tIm2mkbLC82iNOzpVYepGyPmQbbMKVxNvna0jCL3KWFuPoq3s0rBAqEKwunKktVqmLUAhpqTg=" 

SOURCE_CHANNELS = [
    "pressuzb", "shmirziyoyev", "qalampirlive", "uz24newsuz",
    "uzb_meteo", "huquqiyaxborot", "shoubizyangiliklari",
    "pfcsogdianauz", "xavfsizlik_uz", "qisqasitv", "Jizzax_Haydovchilari"
]

TARGET_CHANNEL = "@Sangzoruz1"
TARGET_LINK = "https://t.me/Sangzoruz1"

START_HOUR = 7
END_HOUR = 22
POST_INTERVAL = 600 # 10 daqiqa (soniyalarda)

# Xabarlar navbati
message_queue = deque()

# ================== REKLAMA FILTRI ==================
def clean_ads(text):
    if not text: return ""
    text = re.sub(r'https?://t\.me/\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    ad_words = ["kanalimizga a'zo", "obuna bo'ling", "batafsil o'qing", "manba:", "ssylka"]
    for word in ad_words:
        text = re.compile(re.escape(word), re.IGNORECASE).sub("", text)
    return text.strip()

# ================== OBUNA MATNI ==================
def add_sub_text(text):
    # Matn ostiga obuna bo'lish haqida yozuv qo'shish
    return f"{text}\n\n👉 <a href='{TARGET_LINK}'>Kanalga obuna bo'ling</a>"

# ================== NAVBATNI BOSHQARISH ==================
async def post_manager():
    """Har 15 daqiqada navbatdagi bitta xabarni yuboradi"""
    while True:
        now = datetime.now()
        # Ish vaqti va navbatda xabar borligini tekshirish
        if (START_HOUR <= now.hour < END_HOUR) and message_queue:
            msg_event = message_queue.popleft() # Eng birinchi tushgan xabarni olish
            
            original_text = msg_event.message.message
            cleaned_text = clean_ads(original_text)
            
            if cleaned_text:
                final_text = add_sub_text(cleaned_text)
                try:
                    if msg_event.message.media:
                        await client.send_file(TARGET_CHANNEL, msg_event.message.media, caption=final_text, parse_mode='html')
                    else:
                        await client.send_message(TARGET_CHANNEL, final_text, parse_mode='html', link_preview=False)
                    logging.info("15 daqiqalik interval bilan post yuborildi.")
                except Exception as e:
                    logging.error(f"Yuborishda xatolik: {e}")
        
        # 15 daqiqa kutish
        await asyncio.sleep(POST_INTERVAL)

# ================== TELEGRAM HANDLER ==================
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    # Xabarni shunchaki navbatga qo'shadi
    if event.message.message or event.message.media:
        message_queue.append(event)
        logging.info(f"Yangi xabar navbatga qo'shildi. Navbat soni: {len(message_queue)}")

async def main():
    await client.start()
    print("✅ Bot ishga tushdi va 15 daqiqalik rejimga o'tdi...")
    
    # Post manager funksiyasini fonda ishga tushirish
    client.loop.create_task(post_manager())
    
    await client.run_until_disconnected()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client.loop.run_until_complete(main())