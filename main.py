import asyncio
import logging
import re
import hashlib
from collections import deque
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ================== SOZLAMALAR ==================
API_ID = 25573417
API_HASH = "b56082f4d86578c5a6948c7b964008f9"
SESSION_STRING = "1ApWapzMBuz9TNXmQxy3mkCwJh-Z9os-8Ij3N9CcKl_Xsym0Ec4y58BuoVvHJYzbmJRTwsFAolCd8H6rVKxSGYDoO7EkpA17Sy-OPCMqaf_CW1iv-Tud0qveqIVnb-cWyMw7KWPJER5m4JJCEAOTVQCcXA5v2nUr3AcIxyFPsNLNEAQYPO88NPnOp0G0WA6TdoxgdzvtqZlKMVoAvKLdPfH3rfsSP2D8g7cntDfX1iDWSD7Qd-gcLf9ahSEUPPTYcObdsgPLNoX1BDSM9Zy5ZoUjx7iiaLWfPVIepyUUbsL1lhxzFKJCgyj4TH1hZynuD30KaS1ul0srMnwiLEqt7R6wiTkZX554=" 

ADMIN_ID = 3313699 
SOURCE_CHANNELS = [
    "Rasmiy_xabarlar_Official", "shmirziyoyev", "shoubizyangiliklari", 
    "pfcsogdianauz", "huquqiyaxborot", "uzb_meteo", "xavfsizlik_uz", 
    "qisqasitv", "Jizzax_Haydovchilari", "uzgydromet", "bankxabar", 
    "ozbekiston24", "Jizzax24kanal"
]
TARGET_CHANNEL = "@Sangzoruz1"
TARGET_LINK = "https://t.me/Sangzoruz1"

POST_INTERVAL = 600 
BATCH_SIZE = 5 
message_queue = deque()
processed_hashes = deque(maxlen=200) # Dublikatlarni tekshirish uchun (oxirgi 200 ta xabar)

# ================== FILTRLAR ==================
def clean_ads(text):
    if not text: return ""
    
    # Havolalar va Usernamelarni o'chirish
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    
    # Siz so'ragan maxsus reklama iboralari
    ad_patterns = [
        r"Каналга обуна бўлинг", r"мухим хабарларни биринчи ўқинг", 
        r"энг тезкор хабарлар канали", r"Reklama uchun", r"САҚЛАБ ОЛИНГ", 
        r"ЯҚИНЛАРГА ЮБОРИБ ҚҮЙИНГ", r"Sahifalarimizga obuna bo‘ling",
        r"Каналга қўшилиш", r"Медиабанк", r"Facebook", r"TikTok", r"Instagram",
        r"obuna bo'ling", r"batafsil o'qing", r"manba:", r"quyidagi havola"
    ]
    
    for pattern in ad_patterns:
        text = re.compile(pattern, re.IGNORECASE).sub("", text)
    
    # Ortiqcha bo'shliqlar va qatorlarni tozalash
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def get_message_hash(event):
    """Xabarni takrorlanmasligini tekshirish uchun hash yaratish"""
    content = ""
    if event.message.message:
        # Matnni kichik harf qilib hashlaymiz (ozgina farq bo'lsa ham dublikat deb topishi uchun)
        content += event.message.message[:100].lower() 
    if event.message.media:
        # Medianing o'lchamini qo'shamiz
        if hasattr(event.message.media, 'document'):
            content += str(event.message.media.document.size)
        elif hasattr(event.message.media, 'photo'):
            content += str(event.message.media.photo.id)
            
    return hashlib.md5(content.encode()).hexdigest()

# ================== NAVBATNI BOSHQARISH ==================
async def post_manager():
    await asyncio.sleep(10)
    while True:
        if message_queue:
            for _ in range(BATCH_SIZE):
                if not message_queue: break
                
                msg_event = message_queue.popleft()
                clean_text = clean_ads(msg_event.message.message)
                final_text = f"{clean_text}\n\n👉 <a href='{TARGET_LINK}'>Kanalga obuna bo'ling</a>"
                
                try:
                    # Faqat rasm yoki video bo'lsa yuboradi
                    if msg_event.message.media:
                        await client.send_file(TARGET_CHANNEL, msg_event.message.media, caption=final_text, parse_mode='html')
                    else:
                        await client.send_message(TARGET_CHANNEL, final_text, parse_mode='html', link_preview=False)
                    logging.info("✅ Xabar muvaffaqiyatli yuborildi.")
                except Exception as e:
                    logging.error(f"❌ Yuborishda xato: {e}")
                
                await asyncio.sleep(5) 
            await asyncio.sleep(POST_INTERVAL)
        else:
            await asyncio.sleep(20)

# ================== TELEGRAM HANDLER ==================
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    # Faqat matnli, rasmli yoki videolar qabul qilinadi
    is_media = event.message.photo or event.message.video
    is_text = event.message.message and len(event.message.message) > 10
    
    if is_media or is_text:
        # Dublikatni tekshirish
        msg_hash = get_message_hash(event)
        if msg_hash in processed_hashes:
            logging.info("🚫 Dublikat xabar tashlab ketildi.")
            return
        
        processed_hashes.append(msg_hash)
        message_queue.append(event)
        logging.info(f"📩 Yangi xabar navbatga qo'shildi. (Queue: {len(message_queue)})")

async def main():
    await client.start()
    print("🚀 Bot aktiv! Dublikatlar va reklamalar filtrlanmoqda...")
    client.loop.create_task(post_manager())
    await client.run_until_disconnected()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    client.loop.run_until_complete(main())