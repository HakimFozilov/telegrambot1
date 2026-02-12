import asyncio
import logging
import re
from collections import deque
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ================== SOZLAMALAR ==================
API_ID = 25573417
API_HASH = "b56082f4d86578c5a6948c7b964008f9"
SESSION_STRING = "1ApWapzMBuz9TNXmQxy3mkCwJh-Z9os-8Ij3N9CcKl_Xsym0Ec4y58BuoVvHJYzbmJRTwsFAolCd8H6rVKxSGYDoO7EkpA17Sy-OPCMqaf_CW1iv-Tud0qveqIVnb-cWyMw7KWPJER5m4JJCEAOTVQCcXA5v2nUr3AcIxyFPsNLNEAQYPO88NPnOp0G0WA6TdoxgdzvtqZlKMVoAvKLdPfH3rfsSP2D8g7cntDfX1iDWSD7Qd-gcLf9ahSEUPPTYcObdsgPLNoX1BDSM9Zy5ZoUjx7iiaLWfPVIepyUUbsL1lhxzFKJCgyj4TH1hZynuD30KaS1ul0srMnwiLEqt7R6wiTkZX554=" 

TARGET_CHANNEL = "@Sangzoruz1"
TARGET_LINK = "https://t.me/Sangzoruz1"

SOURCE_CHANNELS = [
    "Rasmiy_xabarlar_Official", "pressuzb", "shmirziyoyev", "uzbprokuratura",
    "shoubizyangiliklari", "pfcsogdianauz", "huquqiyaxborot", "u_generalissimus",
    "uzb_meteo", "xavfsizlik_uz", "qisqasitv", "davlatxizmatchisi_uz",
    "Jizzax_Haydovchilari", "uzgydromet", "uz24newsuz",
    "bankxabar", "ozbekiston24", "Jizzax24kanal", 
]

POST_INTERVAL = 60  # Sinov uchun 1 daqiqa (keyin 900 qilasiz)
message_queue = deque()
processed_albums = set()

# ================== FILTR VA TOZALASH ==================
def clean_ads(text):
    if not text: return ""
    
    # 1. Havolalar va reklamalarni tozalash
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    
    # 2. To'xtatuvchi so'zlar (Agar bo'lsa, xabar umuman yuborilmaydi)
    stop_words = ["sotiladi", "choyxona", "benzin", "qazi", "zapravka", "uztelecom", "aksiya", "narxi", "ijara"]
    for stop in stop_words:
        if stop.lower() in text.lower():
            return None

    # 3. Matn ichidagi keraksiz reklamalar
    ad_patterns = [r"kanalga obuna bo'ling", r"manba:", r"instagram", r"youtube", r"telegramda kuzating", r"yaqinlarga ulashing"]
    for pattern in ad_patterns:
        text = re.compile(pattern, re.IGNORECASE).sub("", text)
    
    # 4. Ortiqcha belgilar
    text = re.sub(r'⚡️|📱|✅|👇', '', text)
    return text.strip()

def add_sub_text(text):
    return f"{text}\n\n👉 <a href='{TARGET_LINK}'>Kanalga obuna bo'ling</a>"

# ================== NAVBATNI BOSHQARISH ==================
async def post_manager():
    logging.info("⚙️ Post manager navbatni tekshirishni boshladi...")
    while True:
        try:
            if message_queue:
                msg_event = message_queue.popleft()
                raw_text = msg_event.message.message or ""
                cleaned = clean_ads(raw_text)
                
                if cleaned is not None:
                    final_text = add_sub_text(cleaned)
                    
                    if msg_event.message.media:
                        # Album bo'lsa ham faqat birinchi mediani yuboradi
                        await client.send_file(TARGET_CHANNEL, msg_event.message.media, caption=final_text, parse_mode='html')
                    else:
                        await client.send_message(TARGET_CHANNEL, final_text, parse_mode='html', link_preview=False)
                    
                    logging.info(f"✅ OK: Xabar @Sangzoruz1 kanaliga chiqdi.")
                    await asyncio.sleep(POST_INTERVAL)
                else:
                    logging.info("🚫 Reklama aniqlandi, o'tkazib yuborildi.")
            else:
                await asyncio.sleep(10) # Navbat bo'sh bo'lsa 10 soniya kutish
        except Exception as e:
            logging.error(f"🚨 Yuborishda xatolik: {e}")
            await asyncio.sleep(20)

# ================== TELEGRAM HANDLER ==================
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    # Album (Media group) bo'lsa
    if event.message.grouped_id:
        gid = event.message.grouped_id
        # Faqat birinchi qismini navbatga qo'shish
        if gid not in processed_albums:
            processed_albums.add(gid)
            message_queue.append(event)
            logging.info(f"📩 Yangi album: Faqat birinchi media navbatga olindi.")
            
            # 1 soatdan keyin keshni tozalash
            async def clear_cache(g_id):
                await asyncio.sleep(3600)
                processed_albums.discard(g_id)
            asyncio.create_task(clear_cache(gid))
    else:
        # Oddiy yakka xabar
        message_queue.append(event)
        logging.info(f"📩 Yangi yakka xabar navbatga olindi.")

async def main():
    await client.start()
    logging.info("🚀 Bot Telegramga ulandi!")
    
    # Ishga tushganini tekshirish uchun kanalga xabar yuboramiz
    try:
        await client.send_message(TARGET_CHANNEL, "🟢 **Bot muvaffaqiyatli ishga tushdi.**\n\nManba kanallardan yangi xabarlar kutilmoqda...", parse_mode='markdown')
    except Exception as e:
        logging.error(f"Test xabari yuborishda xato: {e}")

    client.loop.create_task(post_manager())
    await client.run_until_disconnected()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    try:
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi.")