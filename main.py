import asyncio
import logging
import re
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ================== SOZLAMALAR ==================
API_ID = 25573417
API_HASH = "b56082f4d86578c5a6948c7b964008f9"
# Muhim: Bir marta sessiya yaratib olgach, bu yerga StringSession kodini qo'ying
SESSION_STRING = "1ApWapzMBu3fO0IyfsDsut6GvmfnTy98XJwUaItTW8tjLYkBIetG9iljXhUIx4oLEXwqTfMOw3HEQXQE9msN4W5rdJUAolpfEMUr2W0b1ES5o-505_2BKCc1OWSfw3zYG2rM9TBzDFEBTdAKyT5KzAFgU4hmXMrG68S8hhStMokh8Nh5bai5IkvgO1Wpqt5QKzwy0tTa4zK3BpijZ-5KgRqJJ_PdNsNfNzkT_VXcx6kj6WXQ8Q7v414bOTN7B9YISIN1xaK9cp5EbrvQzHExzE1tIm2mkbLC82iNOzpVYepGyPmQbbMKVxNvna0jCL3KWFuPoq3s0rBAqEKwunKktVqmLUAhpqTg=" 

SOURCE_CHANNELS = [
     "Rasmiy_xabarlar_Official",
    "pressuzb",
    "shmirziyoyev",
    "uzbprokuratura",
    "shoubizyangiliklari",
    "pfcsogdianauz",
    "huquqiyaxborot",
    "u_generalissimus",
    "uzb_meteo",
    "xavfsizlik_uz",
    "qisqasitv",
    "davlatxizmatchisi_uz",
    "Jizzax_Haydovchilari",
    "shov_shuvUZ",
    "uzgydromet",
    "uz24newsuz",
    "bankxabar",
    "jahon_statistikalar",
    "ozbekiston24",
    "foydali_link",
    "Chaqmoq",
]

TARGET_CHANNEL = "@Sangzoruz1"
TARGET_LINK = "https://t.me/Sangzoruz1"

# Ish vaqti: 07:00 dan 22:00 gacha
START_HOUR = 7
END_HOUR = 22

# ================== REKLAMA FILTRI ==================
def clean_ads(text):
    if not text: return ""
    
    # 1. Telegram havolalarini o'chirish (t.me/...)
    text = re.sub(r'https?://t\.me/\S+', '', text)
    # 2. Usernamelarni o'chirish (@username)
    text = re.sub(r'@\w+', '', text)
    # 3. Reklama so'zlarini tozalash
    ad_words = ["kanalimizga a'zo", "obuna bo'ling", "batafsil o'qing", "manba:", "ssylka"]
    for word in ad_words:
        text = re.compile(re.escape(word), re.IGNORECASE).sub("", text)
    
    return text.strip()

# ================== YASHIRIN MANBA ==================
def add_hidden_link(text):
    # Matn oxiriga ko'rinmas havola qo'shish (Yashirin manba)
    hidden_link = f'<a href="{TARGET_LINK}">\u200b</a>' 
    return f"{text}\n\n<b>Manba:</b> <a href='{TARGET_LINK}'>Sangzoruz1</a>{hidden_link}"

# ================== ASOSIY FUNKSIYA ==================
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    now = datetime.now()
    
    # Vaqtni tekshirish (07:00 - 22:00)
    if not (START_HOUR <= now.hour < END_HOUR):
        return

    original_text = event.message.message
    cleaned_text = clean_ads(original_text)
    
    if not cleaned_text:
        return

    final_text = add_hidden_link(cleaned_text)

    try:
        # Agar rasm yoki video bo'lsa
        if event.message.media:
            await client.send_file(
                TARGET_CHANNEL, 
                event.message.media, 
                caption=final_text, 
                parse_mode='html'
            )
        else:
            await client.send_message(
                TARGET_CHANNEL, 
                final_text, 
                parse_mode='html',
                link_preview=False
            )
        logging.info(f"Post yuborildi: {now.strftime('%H:%M:%S')}")
    except Exception as e:
        logging.error(f"Xatolik: {e}")

async def main():
    await client.start()
    print("✅ Bot ishga tushdi...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())