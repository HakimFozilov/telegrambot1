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
BATCH_SIZE = 5      # Har paketda 5 ta xabar
message_queue = deque()

# ================== AQLLI REKLAMA FILTRI ==================
def clean_ads(text):
    if not text: return ""
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    ad_patterns = [
        r"kanalimizga a'zo", r"obuna bo'ling", r"batafsil o'qing", r"manba:", 
        r"ssylka", r"instagram", r"youtube", r"facebook", r"tik tok", r"X\.com",
        r"telegramda kuzating", r"quyidagi havola", r"bizning guruh", r"rasmiy sahifa"
    ]
    for pattern in ad_patterns:
        text = re.compile(pattern, re.IGNORECASE).sub("", text)
    text = re.sub(r'\n\s*\n', '\n\n', text) 
    return text.strip()

def add_sub_text(text):
    clean_text = text if text else "Yangi xabar"
    return f"{clean_text}\n\n👉 <a href='{TARGET_LINK}'>Kanalga obuna bo'ling</a>"

# ================== NAVBATNI BOSHQARISH ==================
async def post_manager():
    await asyncio.sleep(10)
    while True:
        if message_queue:
            for _ in range(BATCH_SIZE):
                if not message_queue:
                    break
                
                msg_event = message_queue.popleft()
                final_text = add_sub_text(clean_ads(msg_event.message.message))
                
                try:
                    if msg_event.message.media:
                        await client.send_file(TARGET_CHANNEL, msg_event.message.media, caption=final_text, parse_mode='html')
                    else:
                        await client.send_message(TARGET_CHANNEL, final_text, parse_mode='html', link_preview=False)
                    logging.info("✅ OK: Xabar kanalga yuborildi.")
                except Exception as e:
                    logging.error(f"❌ Xato: {e}")
                
                await asyncio.sleep(4)
            
            await asyncio.sleep(POST_INTERVAL)
        else:
            await asyncio.sleep(20)

# ================== TELEGRAM HANDLER ==================
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    if event.message.message or event.message.media:
        if len(message_queue) < 200:
            message_queue.append(event)
            logging.info(f"📩 In: Yangi xabar navbatga olindi (Jami: {len(message_queue)})")

async def main():
    await client.start()
    print("🚀 Bot ishga tushdi...")
    try:
        await client.send_message(ADMIN_ID, "🟢 Bot qayta ishga tushdi!")
    except:
        pass
    client.loop.create_task(post_manager())
    await client.run_until_disconnected()

if __name__ == "__main__":
    # Loglarni faqat muhim darajada chiqaramiz
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    try:
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
