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

# Admin ID raqam formatida bo'lishi kerak
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
POST_INTERVAL = 600 # 10 daqiqa

message_queue = deque()

# ================== REKLAMA FILTRI ==================
def clean_ads(text):
    if not text: return ""
    
    # 1. Barcha turdagi havolalarni o'chirish (http, https, t.me, bit.ly va h.k.)
    text = re.sub(r'https?://\S+', '', text)
    
    # 2. Telegram userneymlarini o'chirish (@username)
    text = re.sub(r'@\w+', '', text)
    
    # 3. Ijtimoiy tarmoq nomlari va chaqiriq so'zlarni o'chirish (Katta-kichik harfga qaramaydi)
    ad_patterns = [
        r"kanalimizga a'zo", r"obuna bo'ling", r"batafsil o'qing", r"manba:", 
        r"ssylka", r"instagram", r"youtube", r"facebook", r"tik tok", 
        r"twitter", r"x\.com", r"telegramda kuzating", r"quyidagi havola"
    ]
    
    for pattern in ad_patterns:
        text = re.compile(pattern, re.IGNORECASE).sub("", text)
    
    # 4. Ortiqcha bo'shliqlar va chiziqlarni tozalash
    text = re.sub(r'\n\s*\n', '\n\n', text) # Ketma-ket kelgan bo'sh qatorlarni bittaga tushiradi
    return text.strip()

def add_sub_text(text):
    # Faqat toza matn bo'lsagina pastiga Sangzoruz1 havolasini qo'shadi
    if text:
        return f"{text}\n\n👉 <a href='{TARGET_LINK}'>Kanalga obuna bo'ling</a>"
    return ""
    
# ================== NAVBATNI BOSHQARISH ==================
async def post_manager():
    while True:
        now = datetime.now()
        # Ish vaqti va navbatda xabar borligini tekshirish
        if (START_HOUR <= now.hour < END_HOUR) and message_queue:
            logging.info(f"Navbatni bo'shatish boshlandi. Hozirgi navbat: {len(message_queue)}")
            
            # Har 10 daqiqada maksimal 5 ta xabar yuborish
            for _ in range(5):
                if not message_queue: # Agar navbat bo'shab qolsa, to'xtash
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
                        logging.info("Xabar paket tarkibida yuborildi.")
                    except Exception as e:
                        logging.error(f"Yuborishda xatolik: {e}")
                
                # Paket ichidagi xabarlar orasida 3 soniya kutish (Telegram bloklamasligi uchun)
                await asyncio.sleep(3)
            
            logging.info(f"Paket yuborildi. Qolgan navbat: {len(message_queue)}")
        
        # Keyingi paketgacha 10 daqiqa kutish
        await asyncio.sleep(POST_INTERVAL)

# ================== TELEGRAM HANDLER ==================
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    if event.message.message or event.message.media:
        message_queue.append(event)
        logging.info(f"Yangi xabar navbatga qo'shildi. Navbat: {len(message_queue)}")

async def main():
    await client.start()
    print("✅ Bot ulandi...")

    # Admin xabarini yuborishda xatolik botni to'xtatib qo'ymasligi uchun try-except
    try:
        start_msg = f"🚀 **Bot ishga tushdi!**\n🕒 Vaqt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n✅ Kanallarni kuzatish boshlandi."
        await client.send_message(ADMIN_ID, start_msg)
    except Exception as e:
        logging.warning(f"Adminga start xabari yuborilmadi (ID topilmadi): {e}")

    client.loop.create_task(post_manager())
    
    try:
        await client.run_until_disconnected()
    finally:
        if client.is_connected():
            try:
                stop_msg = f"⚠️ **Bot ishdan to'xtadi!**\n🕒 Vaqt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                await client.send_message(ADMIN_ID, stop_msg)
            # ignore
            except: pass
        print("🔴 Bot to'xtatildi.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass