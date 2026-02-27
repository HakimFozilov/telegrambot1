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
# Session stringdagi ortiqcha bo'shliqlarni olib tashlaymiz
SESSION_STRING = "1ApWapzMBuz9TNXmQxy3mkCwJh-Z9os-8Ij3N9CcKl_Xsym0Ec4y58BuoVvHJYzbmJRTwsFAolCd8H6rVKxSGYDoO7EkpA17Sy-OPCMqaf_CW1iv-Tud0qveqIVnb-cWyMw7KWPJER5m4JJCEAOTVQCcXA5v2nUr3AcIxyFPsNLNEAQYPO88NPnOp0G0WA6TdoxgdzvtqZlKMVoAvKLdPfH3rfsSP2D8g7cntDfX1iDWSD7Qd-gcLf9ahSEUPPTYcObdsgPLNoX1BDSM9Zy5ZoUjx7iiaLWfPVIepyUUbsL1lhxzFKJCgyj4TH1hZynuD30KaS1ul0srMnwiLEqt7R6wiTkZX554=".strip()

ADMIN_ID = 3313699 
# XATO TUZATILDI: Kanallar oldiga @ belgisi qo'shildi
SOURCE_CHANNELS = [
    "@Rasmiy_xabarlar_Official", "@shoubizyangiliklari", 
    "@huquqiyaxborot", "@uzb_meteo", "@xavfsizlik_uz", 
    "@qisqasitv", "@Jizzax_Haydovchilari", "@bankxabar", "@Jurnalist24uz",
    "@Jizzax24kanal"
]
TARGET_CHANNEL = "@Sangzoruz1"
TARGET_LINK = "https://t.me/Sangzoruz1"

POST_INTERVAL = 1200 
BATCH_SIZE = 5 
message_queue = deque()
processed_hashes = deque(maxlen=300)

# ================== FILTRLAR ==================

def is_commercial_ad(text):
    if not text: return False
    ad_keywords = [
        r"sotiladi", r"яшаш шароити", r"ижара", r"манзил:", r"мўлжал", r"балиқ", 
        r"baliq", r"qazi", r"saharlik", r"📱 📱 📱 📱",
        r"ошхона", r"кафе", r"ресторан", r"buyurtma berish", r"етказиб бериш", 
        r"@Jurnalist24uz", r"тел:", r"moshina", r"лизинг", r"кредит", 
        r"хонадон", r"уй сотилади", r"mdf", r"Каналга обуна булинг", 
        r"Sahifalarimizga obuna bo‘ling", r"qisqasitv", r"instagram\.com", r"tiktok\.com", r"youtube\.com"
    ]
    for word in ad_keywords:
        if re.search(word, text, re.IGNORECASE):
            return True
    return False

def clean_ads(text):
    if not text: return ""
    # Linklar va userlarni tozalash
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    # Belgilarni tozalash
    text = re.sub(r'[⚡️👇❗👈👉✅🔹🔸➖]|\-\-\-', '', text)
    
    ad_patterns = [
        r"Каналга обуна бўлинг", r"мухим хабарларни биринчи ўқинг", 
        r"энг тезкор хабарлар канали", r"аъзо бўлинг", r"Sahifalarimizga obuna bo‘ling",
        r"Медиабанк", r"Facebook", r"TikTok", r"Instagram", r"YouTube", r"X\.com", r"Telegram",
        r"t\.me", r"obuna bo'ling", r"reklama", r"САҚЛАБ ОЛИНГ", r"– га", 
        r"ЯҚИНЛАРГА ЮБОРИБ ҚЎЙИНГ", r"саҳифаларимизга"
    ]
    for pattern in ad_patterns:
        text = re.compile(pattern, re.IGNORECASE).sub("", text)
    
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def get_message_hash(event):
    content = ""
    if event.message.message:
        # Faqat matnli qismidan hash olish
        clean_txt = clean_ads(event.message.message)[:50].lower()
        content += clean_txt
    if event.message.media:
        # Media turiga qarab ID qo'shish
        if hasattr(event.message.media, 'document'):
            content += str(event.message.media.document.id)
        elif hasattr(event.message.media, 'photo'):
            content += str(event.message.media.photo.id)
    return hashlib.md5(content.encode()).hexdigest()

# ================== NAVBATNI BOSHQARISH ==================

async def post_manager():
    await asyncio.sleep(5)
    while True:
        if message_queue:
            for _ in range(BATCH_SIZE):
                if not message_queue: break
                
                msg_event = message_queue.popleft()
                raw_text = msg_event.message.message or ""
                
                if is_commercial_ad(raw_text):
                    logging.info("🛑 Reklama filtri ishladi.")
                    continue

                clean_text = clean_ads(raw_text)
                final_text = clean_text if clean_text else "Yangilik"
                final_text += f"\n\n👉 <a href='{TARGET_LINK}'>Sangzoruz1 - Kanalga obuna bo'ling</a>"
                
                try:
                    # Media borligini tekshirish
                    if msg_event.message.media:
                        await client.send_file(TARGET_CHANNEL, msg_event.message.media, caption=final_text, parse_mode='html')
                    else:
                        await client.send_message(TARGET_CHANNEL, final_text, parse_mode='html', link_preview=False)
                    logging.info("✅ Xabar yuborildi.")
                except Exception as e:
                    logging.error(f"❌ Yuborishda xato: {e}")
                
                await asyncio.sleep(4)
            await asyncio.sleep(POST_INTERVAL)
        else:
            await asyncio.sleep(10)

# ================== TELEGRAM HANDLER ==================

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    # Xabarda matn yoki media borligini aniqroq tekshirish
    has_media = event.message.media is not None
    has_text = bool(event.message.message and len(event.message.message) > 5)

    if has_media or has_text:
        m_hash = get_message_hash(event)
        if m_hash in processed_hashes:
            return
        
        processed_hashes.append(m_hash)
        message_queue.append(event)
        logging.info(f"📩 Navbatga qo'shildi. (Jami: {len(message_queue)})")

async def main():
    # Sessiyani boshlash
    await client.start()
    print("🚀 Bot ishga tushdi...")
    # Post managerni alohida task qilib ishga tushirish
    asyncio.create_task(post_manager())
    await client.run_until_disconnected()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    try:
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("🛑 Bot to'xtatildi.")
