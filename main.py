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

ADMIN_ID = 3313699 

SOURCE_CHANNELS = [
    "Rasmiy_xabarlar_Official", "pressuzb", "shmirziyoyev", "uzbprokuratura",
    "shoubizyangiliklari", "pfcsogdianauz", "huquqiyaxborot", "u_generalissimus",
    "uzb_meteo", "xavfsizlik_uz", "qisqasitv", "davlatxizmatchisi_uz",
    "Jizzax_Haydovchilari", "shov_shuvUZ", "uzgydromet", "uz24newsuz",
    "bankxabar", "jahon_statistikalar", "ozbekiston24", "foydali_link", "Chaqmoq"
]

TARGET_CHANNEL = "@Sangzoruz1"
TARGET_LINK = "https://t.me/Sangzoruz1"

START_HOUR = 7
END_HOUR = 22
POST_INTERVAL = 600 # 10 daqiqa (600 soniya)
BATCH_SIZE = 5      # Har safar yuboriladigan xabarlar soni

message_queue = deque()

# ================== KUCHAYTIRILGAN FILTR ==================
def clean_ads(text):
    if not text: return ""
    
    # 1. Barcha turdagi havolalarni o'chirish (http, https, t.me va h.k.)
    text = re.sub(r'https?://\S+', '', text)
    
    # 2. Telegram userneymlarini o'chirish (@username)
    text = re.sub(r'@\w+', '', text)
    
    # 3. Ijtimoiy tarmoqlar va reklama so'zlarni o'chirish
    ad_patterns = [
        r"kanalimizga a'zo", r"obuna bo'ling", r"batafsil o'qing", r"manba:", 
        r"ssylka", r"instagram", r"youtube", r"facebook", r"tik tok", 
        r"twitter", r"x\.com", r"telegramda kuzating", r"quyidagi havola",
        r"bizning guruh", r"rasmiy sahifa", r"bizga qo'shiling"
    ]
    
    for pattern in ad_patterns:
        text = re.compile(pattern, re.IGNORECASE).sub("", text)
    
    # 4. Ortiqcha bo'shliqlar va chiziqlarni tozalash
    text = re.sub(r'\n\s*\n', '\n\n', text) 
    return text.strip()

def add_sub_text(text):
    if text:
        return f"{text}\n\n👉 <a href='{TARGET_LINK}'>Kanalga obuna bo'ling</a>"
    return ""

# ================== NAVBATNI BOSHQARISH ==================
async def post_manager():
    # Bot ishga tushganda navbat biroz yig'ilishi uchun qisqa kutish
    await asyncio.sleep(10)
    
    while True:
        now = datetime.now()
        
        # Ish vaqti ekanligini tekshirish
        if START_HOUR <= now.hour < END_HOUR:
            if message_queue:
                logging.info(f"Paketli yuborish boshlandi. Jami navbat: {len(message_queue)}")
                
                for _ in range(BATCH_SIZE):
                    if not message_queue:
                        break
                    
                    msg_event = message_queue.popleft()
                    original_text = msg_event.message.message
                    cleaned_text = clean_ads(original_text)
                    
                    if cleaned_text:
                        final_text = add_sub_text(cleaned_text)
                        try:
                            if msg_event.message.media:
                                await client.send_file(TARGET_CHANNEL, msg_event.message.media, caption=final_text, parse_mode='html')
                            else:
                                await client.send_message(TARGET_CHANNEL, final_text, parse_mode='html', link_preview=False)
                            logging.info("Xabar muvaffaqiyatli yuborildi.")
                        except Exception as e:
                            logging.error(f"Yuborishda xatolik: {e}")
                    
                    # Telegram cheklovi uchun xabarlar orasida 3 soniya kutish
                    await asyncio.sleep(3)
                
                logging.info(f"Paket yuborildi. Keyingi paketgacha {POST_INTERVAL//60} daqiqa tanaffus.")
                await asyncio.sleep(POST_INTERVAL)
            else:
                # Navbat bo'sh bo'lsa, har 30 soniyada tekshirish
                await asyncio.sleep(30)
        else:
            # Ish vaqtidan tashqari bo'lsa, har 10 daqiqada tekshirish
            await asyncio.sleep(600)

# ================== TELEGRAM HANDLER ==================
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    if event.message.message or event.message.media:
        # Navbatni 200 tadan oshirmaymiz (xotira uchun)
        if len(message_queue) < 200:
            message_queue.append(event)
            logging.info(f"Yangi xabar navbatga tushdi. Navbat: {len(message_queue)}")

async def main():
    await client.start()
    print("✅ Bot ulandi va ishga tushdi...")

    # Admin xabari (xavfsiz)
    try:
        start_msg = f"🚀 **Bot mukammal rejimda ishga tushdi!**\n📦 Paket hajmi: {BATCH_SIZE}\n⏱ Interval: {POST_INTERVAL//60} daqiqa."
        await client.send_message(ADMIN_ID, start_msg)
    except:
        pass

    client.loop.create_task(post_manager())
    await client.run_until_disconnected()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass