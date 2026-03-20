import asyncio
import logging
import re
import hashlib
import datetime
import pytz
from collections import deque
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ================== SOZLAMALAR ==================
API_ID = 34696814
API_HASH = "f6c213e017169b70c8465143d1751ea2"
SESSION_STRING = "1ApWapzMBu8B7W6OmcgHjwN2K09ZCsYMtC7RTmAKplo-84c9n4NLFEwklYZCUzO-IOmPHtGDGAeWvnu2gln-mcrLznvk3gbZpyyGLh9remfxX7D8ifanj8FjfyDDcRK52aKom-NlXNwHR5vqXHca72GskI1xQMWAj7rg2hqMwI_bKNely-AGk-fCa5nf8L0bgpACheTWEmQvAQXlxwI2dKKdfmK4dVBS2e15SsX1qQuS5a_0e7vF3-qtVhkvBrJe3KktB3BGpY9Y45IxoQY8gQzLQMz8n8jvTBp7XYXsfGtyRAYdxDokuqEGKVb_9lT9GwgEOJ_S9gqbx18ktoaijuS7uSWSj50A=".strip()

# LOGLARNI QABUL QILUVCHI BOT YOKI USER ID (O'zingizning ID raqamingiz bo'lishi tavsiya etiladi)
LOG_TARGET = "@SangzorReposterBot" 

ADMIN_ID = 5747999018
SOURCE_CHANNELS = [
    "@Rasmiy_xabarlar_Official", "@shoubizyangiliklari", 
    "@huquqiyaxborot", "@uzb_meteo", "@xavfsizlik_uz", 
    "@qisqasitv", "@Jizzax_Haydovchilari", "@bankxabar", 
    "@Jurnalist24uz", "@Jizzax24kanal"
]
TARGET_CHANNEL = "@Sangzoruz1"
TARGET_LINK = "https://t.me/Sangzoruz1"

POST_INTERVAL = 120 
BATCH_SIZE = 1 
message_queue = deque()
processed_hashes = deque(maxlen=300)

# ================== TELEGRAM LOG HANDLER ==================

class TelegramLogHandler(logging.Handler):
    """Loglarni Telegram kanalga yoki botga yuborish uchun handler"""
    def __init__(self, client, target):
        super().__init__()
        self.client = client
        self.target = target
        self.loop = asyncio.get_event_loop()

    def emit(self, record):
        log_entry = self.format(record)
        # Faqat muhim loglarni yuboramiz (xatolik yoki muvaffaqiyatli post)
        if "OK:" in log_entry or "Xato:" in log_entry or "Reklama" in log_entry:
            self.loop.create_task(self.send_log(log_entry))

    async def send_log(self, message):
        try:
            # Xabarni qisqaroq va chiroyli qilish
            clean_msg = f"<code>{message}</code>"
            await self.client.send_message(self.target, clean_msg, parse_mode='html')
        except Exception:
            pass # Log yuborishda xato bo'lsa, cheksiz siklga tushmaslik uchun indamaymiz

# ================== FILTRLAR (Oldingidek) ==================

def is_commercial_ad(text):
    if not text: return False
    ad_keywords = [
        r"sotiladi", r"яшаш шароити", r"ижара", r"манзил:", r"мўлжал", r"балиқ", 
        r"baliq", r"qazi", r"saharlik", r"📱 📱 📱 📱",
        r"ошхона", r"кафе", r"ресторан", r"buyurtma berish", r"етказиб бериш", 
        r"@Jurnalist24uz", r"тел:", r"moshina", r"лизинг", r"кредит", r"avaz oxun",
        r"хонадон", r"уй сотилади", r"mdf", r"Каналга обуна булинг", r"texnomart", 
        r"Sahifalarimizga obuna bo‘ling", r"qisqasitv", r"instagram\.com", r"tiktok\.com", r"youtube\.com"
    ]
    for word in ad_keywords:
        if re.search(word, text, re.IGNORECASE):
            return True
    return False

def clean_ads(text):
    if not text: return ""
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'@\w+', '', text)
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
        clean_txt = clean_ads(event.message.message)[:50].lower()
        content += clean_txt
    if event.message.media:
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
                    logging.info(f"🛑 Reklama aniqlandi: {raw_text[:30]}...")
                    continue

                clean_text = clean_ads(raw_text)
                
                if not clean_text or len(clean_text) < 5:
                    logging.info("⚠️ Foydali matn qolmagani uchun bekor qilindi.")
                    continue

                final_caption = f"{clean_text}\n\n👉 <a href='{TARGET_LINK}'>Sangzoruz1 - Kanalga obuna bo'ling</a>"
                
                try:
                    if msg_event.message.media:
                        await client.send_file(TARGET_CHANNEL, msg_event.message.media, caption=final_caption, parse_mode='html')
                    else:
                        await client.send_message(TARGET_CHANNEL, final_caption, parse_mode='html', link_preview=False)
                    
                    logging.info(f"✅ OK: Xabar kanalga yuborildi.")
                except Exception as e:
                    logging.error(f"❌ Xato: {e}")
                
                await asyncio.sleep(4)
            await asyncio.sleep(POST_INTERVAL)
        else:
            await asyncio.sleep(10)

# ================== TELEGRAM HANDLER ==================

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    m_hash = get_message_hash(event)
    if m_hash in processed_hashes:
        return
    
    processed_hashes.append(m_hash)
    message_queue.append(event)
    logging.info(f"📩 Navbatga olindi. (Navbatda: {len(message_queue)})")

async def main():
    await client.start()
    
    # Log handlerni sozlash
    tg_handler = TelegramLogHandler(client, LOG_TARGET)
    tg_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    logging.getLogger().addHandler(tg_handler)
    
    print("🚀 Bot ishlamoqda...")
    logging.info("🚀 Bot tizimga muvaffaqiyatli ulandi.")
    
    asyncio.create_task(post_manager())
    await client.run_until_disconnected()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    try:
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("🛑 To'xtatildi.")
