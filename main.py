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

ADMIN_ID = 3313699 
SOURCE_CHANNELS = [
    "Rasmiy_xabarlar_Official", "pressuzb", "shmirziyoyev", "uzbprokuratura",
    "shoubizyangiliklari", "pfcsogdianauz", "huquqiyaxborot", "u_generalissimus",
    "uzb_meteo", "xavfsizlik_uz", "qisqasitv", "davlatxizmatchisi_uz",
    "Jizzax_Haydovchilari", "uzgydromet", "uz24newsuz",
    "bankxabar", "ozbekiston24", "Jizzax24kanal", 
]

TARGET_CHANNEL = "@Sangzoruz1"
TARGET_LINK = "https://t.me/Sangzoruz1"

POST_INTERVAL = 600 # 10 daqiqa
message_queue = deque()
processed_albums = set() # Albumlarni filtr qilish uchun

# ================== FILTR VA TOZALASH ==================
def clean_ads(text):
    if not text: return ""
    
    # Havolalar va reklamalarni tozalash
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    
    stop_words = ["sotiladi", "choyxona", "benzin", "qazi", "zapravka", "uztelecom", "aksiya", "narxi"]
    for stop in stop_words:
        if stop.lower() in text.lower():
            return None

    ad_patterns = [r"kanalga obuna bo'ling", r"manba:", r"instagram", r"youtube", r"telegramda kuzating"]
    for pattern in ad_patterns:
        text = re.compile(pattern, re.IGNORECASE).sub("", text)
    
    text = re.sub(r'⚡️|📱|✅|👇', '', text)
    return text.strip()

def add_sub_text(text):
    return f"{text}\n\n👉 <a href='{TARGET_LINK}'>Kanalga obuna bo'ling</a>"

# ================== NAVBATNI BOSHQARISH ==================
async def post_manager():
    logging.info("⚙️ Post manager ishga tushdi...")
    while True:
        try:
            if message_queue:
                msg_event = message_queue.popleft()
                
                raw_text = msg_event.message.message or ""
                cleaned = clean_ads(raw_text)
                
                if cleaned is not None:
                    final_text = add_sub_text(cleaned)
                    
                    if msg_event.message.media:
                        # Faqat bitta fayl yuborish (media group bo'lsa ham)
                        await client.send_file(TARGET_CHANNEL, msg_event.message.media, caption=final_text, parse_mode='html')
                    else:
                        await client.send_message(TARGET_CHANNEL, final_text, parse_mode='html', link_preview=False)
                    
                    logging.info("✅ OK: Xabar yuborildi.")
                    await asyncio.sleep(POST_INTERVAL)
                else:
                    logging.info("🚫 Reklama topildi, xabar tashlab ketildi.")
            else:
                await asyncio.sleep(5)
        except Exception as e:
            logging.error(f"🚨 Managerda xatosi: {e}")
            await asyncio.sleep(10)

# ================== TELEGRAM HANDLER ==================
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    # Agar xabar albumning bir qismi bo'lsa
    if event.message.grouped_id:
        gid = event.message.grouped_id
        # Agar bu albumning birinchi kelgan qismi bo'lsa, qabul qilamiz
        if gid not in processed_albums:
            processed_albums.add(gid)
            message_queue.append(event)
            logging.info(f"📩 Album keldi, faqat birinchi qismi olindi.")
            
            # Xotirani tozalash (1 soatdan keyin album ID sini o'chiramiz)
            async def clear_id(g_id):
                await asyncio.sleep(3600)
                processed_albums.discard(g_id)
            asyncio.create_task(clear_id(gid))
    else:
        # Oddiy yakka xabar
        message_queue.append(event)
        logging.info(f"📩 Oddiy xabar navbatga olindi.")

async def main():
    await client.start()
    print("🚀 Bot Sangzoruz1 uchun (Faqat bitta rasm rejimi) ishga tushdi...")
    client.loop.create_task(post_manager())
    await client.run_until_disconnected()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    try:
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
