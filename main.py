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

POST_INTERVAL = 900 # 15 daqiqa (Buni test uchun 60 qilib ko'ring)
message_queue = deque()
album_storage = {}
pending_tasks = {}

# ================== FILTR VA TOZALASH ==================
def clean_ads(text):
    if not text: return ""
    
    # 1. Havolalar va foydalanuvchi nomlarini o'chirish
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    
    # 2. To'liq o'chirib tashlanadigan reklama so'zlari
    stop_words = [
        "sotiladi", "choyxona", "benzin", "qazi", "zapravka", "uztelecom", 
        "aksiya", "narxi", "pulingizni", "uy sotiladi", "ijaraga beriladi"
    ]
    for stop in stop_words:
        if stop.lower() in text.lower():
            return None

    # 3. Reklama "quyruqlari"
    ad_patterns = [
        r"kanalga obuna bo'ling", r"a'zo bo'ling", r"batafsil o'qing", 
        r"manba:", r"ssylka", r"instagram", r"youtube", r"facebook", 
        r"tik tok", r"X\.com", r"telegramda kuzating", r"quyidagi havola", 
        r"bizning guruh", r"rasmiy sahifa", r"eng tezkor xabar", r"yaqinlarga ulashing"
    ]
    for pattern in ad_patterns:
        text = re.compile(pattern, re.IGNORECASE).sub("", text)
    
    text = re.sub(r'⚡️|📱|✅|👇', '', text)
    text = re.sub(r'\n\s*\n', '\n\n', text) 
    
    return text.strip()

def add_sub_text(text):
    if not text: return f"👉 <a href='{TARGET_LINK}'>Kanalga obuna bo'ling</a>"
    return f"{text}\n\n👉 <a href='{TARGET_LINK}'>Kanalga obuna bo'ling</a>"

# ================== NAVBATNI BOSHQARISH ==================
async def post_manager():
    logging.info("⚙️ Post manager ishga tushdi...")
    while True:
        try:
            if message_queue:
                msg_data = message_queue.popleft()
                
                # Media-gruppa (album) bo'lsa
                if isinstance(msg_data, list):
                    first_msg = msg_data[0]
                    caption = clean_ads(first_msg.message.message)
                    if caption is not None:
                        final_caption = add_sub_text(caption)
                        files = [m.message.media for m in msg_data if m.message.media]
                        await client.send_file(TARGET_CHANNEL, files, caption=final_caption, parse_mode='html')
                        logging.info("✅ OK: Media-gruppa yuborildi.")
                
                # Yakka xabar bo'lsa
                else:
                    raw_text = msg_data.message.message
                    cleaned = clean_ads(raw_text)
                    if cleaned is not None:
                        final_text = add_sub_text(cleaned)
                        if msg_data.message.media:
                            await client.send_file(TARGET_CHANNEL, msg_data.message.media, caption=final_text, parse_mode='html')
                        else:
                            await client.send_message(TARGET_CHANNEL, final_text, parse_mode='html', link_preview=False)
                        logging.info("✅ OK: Yakka xabar yuborildi.")
                
                await asyncio.sleep(POST_INTERVAL)
            else:
                await asyncio.sleep(5) # Navbat bo'sh bo'lsa kutish
        except Exception as e:
            logging.error(f"🚨 Managerda xatolik: {e}")
            await asyncio.sleep(10)

# ================== TELEGRAM HANDLER ==================
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    # Media-gruppa bo'lsa
    if event.message.grouped_id:
        gid = event.message.grouped_id
        if gid not in album_storage:
            album_storage[gid] = []
            
            async def wait_and_add(g_id):
                await asyncio.sleep(5) # Barcha qismlarni kutish (5 sek yetarli)
                if g_id in album_storage:
                    message_queue.append(list(album_storage[g_id]))
                    logging.info(f"📩 Album navbatga qo'shildi (ID: {g_id})")
                    del album_storage[g_id]
                    if g_id in pending_tasks: del pending_tasks[g_id]

            if gid not in pending_tasks:
                pending_tasks[gid] = asyncio.create_task(wait_and_add(gid))
        
        album_storage[gid].append(event)
        
    else:
        # Yakka xabar
        if event.message.message or event.message.media:
            message_queue.append(event)
            logging.info(f"📩 Yangi xabar navbatga olindi.")

async def main():
    await client.start()
    logging.info("🚀 Bot @Sangzoruz1 uchun muvaffaqiyatli ishga tushdi!")
    client.loop.create_task(post_manager())
    await client.run_until_disconnected()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    try:
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi.")
