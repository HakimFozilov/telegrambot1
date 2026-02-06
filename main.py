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
# Diqqat: Yangi SESSION_STRING kodingizni bu yerga to'liq qo'ying
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

# 24 soatlik ish rejimi
START_HOUR = 0
END_HOUR = 24
POST_INTERVAL = 600 # 10 daqiqa
BATCH_SIZE = 5      # Har paketda 5 ta xabar

message_queue = deque()

# ================== AQLLI REKLAMA FILTRI ==================
def clean_ads(text):
    if not text: return ""
    
    # 1. Barcha turdagi havolalarni (http/https) o'chirish
    text = re.sub(r'https?://\S+', '', text)
    
    # 2. Telegram userneymlarini o'chirish (@username)
    text = re.sub(r'@\w+', '', text)
    
    # 3. Reklama so'zlari va ijtimoiy tarmoqlarni o'chirish
    ad_patterns = [
        r"kanalimizga a'zo", r"obuna bo'ling", r"batafsil o'qing", r"manba:", 
        r"ssylka", r"instagram", r"youtube", r"facebook", r"tik tok", 
        r"twitter", r"x\.com", r"telegramda kuzating", r"quyidagi havola",
        r"bizning guruh", r"rasmiy sahifa", r"bizga qo'shiling"
    ]
    
    for pattern in ad_patterns:
        text = re.compile(pattern, re.IGNORECASE).sub("", text)
    
    # 4. Ortiqcha bo'sh qatorlarni bittaga tushirish
    text = re.sub(r'\n\s*\n', '\n\n', text) 
    return text.strip()

def add_sub_text(text):
    # Agar matn filtrdan keyin bo'sh qolgan bo'lsa ham kanal havolasini qo'shamiz
    clean_text = text if text else "Yangi xabar"
    return f"{clean_text}\n\n👉 <a href='{TARGET_LINK}'>Kanalga obuna bo'ling</a>"

# ================== NAVBATNI BOSHQARISH ==================
async def post_manager():
    logging.info("🚀 Post manager ishga tushdi...")
    # Bot yoqilganda xabarlar yig'ilishi uchun 15 soniya kutamiz
    await asyncio.sleep(15)
    
    while True:
        if message_queue:
            logging.info(f"🔄 Navbatda {len(message_queue)} ta xabar bor. Paket yuborish boshlandi...")
            
            for _ in range(BATCH_SIZE):
                if not message_queue:
                    break
                
                msg_event = message_queue.popleft()
                original_text = msg_event.message.message
                
                # Tozalangan matnni tayyorlash
                cleaned = clean_ads(original_text)
                final_text = add_sub_text(cleaned)
                
                try:
                    if msg_event.message.media:
                        await client.send_file(TARGET_CHANNEL, msg_event.message.media, caption=final_text, parse_mode='html')
                    else:
                        await client.send_message(TARGET_CHANNEL, final_text, parse_mode='html', link_preview=False)
                    logging.info("✅ Xabar kanalga muvaffaqiyatli chiqdi.")
                except Exception as e:
                    logging.error(f"❌ Yuborishda xatolik: {e}")
                
                # Telegram cheklovi uchun qisqa kutish
                await asyncio.sleep(4)
            
            logging.info(f"⏱ Paket tugadi. Navbatda {len(message_queue)} ta qoldi. {POST_INTERVAL} soniya tanaffus.")
            await asyncio.sleep(POST_INTERVAL)
        else:
            # Navbat bo'sh bo'lsa har 20 soniyada tekshirib turish
            await asyncio.sleep(20)

# ================== TELEGRAM HANDLER ==================
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    if event.message.message or event.message.media:
        # Xotirani himoya qilish uchun navbatni 200 tadan oshirmaymiz
        if len(message_queue) < 200:
            message_queue.append(event)
            logging.info(f"📩 Yangi xabar tutildi. Navbat: {len(message_queue)}")

async def main():
    await client.start()
    print("✅ Bot Telegramga muvaffaqiyatli ulandi!")

    try:
        start_msg = f"🟢 **Bot 24/7 rejimida ishga tushdi!**\n📊 Paket hajmi: {BATCH_SIZE}\n⏱ Tanaffus: {POST_INTERVAL//60} daqiqa."
        await client.send_message(ADMIN_ID, start_msg)
    except:
        pass

    # Post manager-ni alohida vazifa sifatida ishga tushiramiz
    client.loop.create_task(post_manager())
    await client.run_until_disconnected()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    try:
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass