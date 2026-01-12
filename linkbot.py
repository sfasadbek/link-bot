import asyncio
import os
import logging
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import yt_dlp

# 1. SOZLAMALAR
TOKEN = "8429904690:AAHYJsFVU4gkYQWNwYZyk-7M2zTFiYvmmMk"
ADMIN_ID = 6741153061
CHANNELS = ["@iiv_qonuni"] 

bot = Bot(token=TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# Foydalanuvchi holatlarini saqlash uchun
class SupportState(StatesGroup):
    waiting_for_message = State()

users_db = {} 

def clean_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

async def check_sub(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["member", "administrator", "creator"]:
                return True
        except Exception:
            return False
    return False

def main_reply_keyboard():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Yordam 🆘")]], resize_keyboard=True)

def sub_keyboard():
    buttons = [[InlineKeyboardButton(text="Kanalga a'zo bo'lish ➕", url="https://t.me/iiv_qonuni")],
               [InlineKeyboardButton(text="Tasdiqlash ✅", callback_data="check_subscription")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def search_music(query):
    ydl_opts = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True, 'extract_flat': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch5:{query}", download=False)
        return info['entries']

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    if await check_sub(message.from_user.id) or message.from_user.id == ADMIN_ID:
        await message.answer("👋 Salom! Video linkini yuboring yoki qo'shiq nomini yozing.", reply_markup=main_reply_keyboard())
    else:
        await message.answer("⚠️ Botdan foydalanish uchun kanalimizga a'zo bo'ling:", reply_markup=sub_keyboard())

@dp.callback_query(F.data == "check_subscription")
async def check_callback(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.delete()
        await call.message.answer("✅ Raxmat! Obuna tasdiqlandi.", reply_markup=main_reply_keyboard())
    else:
        await call.answer("❌ Siz hali obuna bo'lmadingiz!", show_alert=True)

# YORDAM TUGMASI BOSILGANDA
@dp.message(F.text == "Yordam 🆘")
async def help_handler(message: types.Message, state: FSMContext):
    await message.answer("📝 Adminga xabar yoki taklifingizni yozib yuboring:")
    await state.set_state(SupportState.waiting_for_message)

# ADMINGA XABAR YUBORISH
@dp.message(SupportState.waiting_for_message)
async def forward_to_admin(message: types.Message, state: FSMContext):
    info = f"📩 YANGI XABAR\n👤 Kimdan: {message.from_user.full_name}\n🆔 ID: `{message.from_user.id}`\n\n📝 Xabar: {message.text}"
    sent_msg = await bot.send_message(chat_id=ADMIN_ID, text=info)
    
    # Kelajakda javob berish uchun IDni saqlaymiz
    users_db[sent_msg.message_id] = message.from_user.id
    
    await message.answer("✅ Xabaringiz adminga yuborildi. Tez orada javob olasiz.")
    await state.clear()

@dp.callback_query(F.data.startswith("music_"))
async def download_music_callback(call: types.CallbackQuery):
    video_id = call.data.split("_")[1]
    url = f"https://www.youtube.com/watch?v={video_id}"
    status = await call.message.answer("📥 Musiqa yuklanmoqda...")
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = clean_filename(info.get('title', 'music'))
        filename = f"{title}.m4a"
        ydl_opts = {'format': 'bestaudio/best', 'outtmpl': filename}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await asyncio.to_thread(ydl.download, [url])
        await call.message.answer_audio(types.FSInputFile(filename))
        await status.delete()
        if os.path.exists(filename): os.remove(filename)
    except Exception:
        await status.edit_text("❌ Yuklashda xatolik!")

@dp.message()
async def handle_all(message: types.Message):
    # ADMIN JAVOB BERISHI (Reply orqali)
    if message.reply_to_message and message.from_user.id == ADMIN_ID:
        reply_id = message.reply_to_message.message_id
        if reply_id in users_db:
            user_id = users_db[reply_id]
            try:
                await bot.send_message(chat_id=user_id, text=f"📩 Admin javobi:\n\n{message.text}")
                await message.answer("✅ Javobingiz yuborildi.")
            except Exception:
                await message.answer("❌ Foydalanuvchiga yuborib bo'lmadi.")
        return

    # ODDIY FOYDALANUVCHILAR UCHUN
    if message.from_user.id != ADMIN_ID:
        if not await check_sub(message.from_user.id):
            await message.answer("⚠️ Avval kanalga a'zo bo'ling:", reply_markup=sub_keyboard())
            return

    # LINK BO'LSA
    if message.text and ("http" in message.text):
        status = await message.answer("⏳ Video yuklanmoqda...")
        try:
            ydl_opts = {'format': 'best', 'outtmpl': 'video.mp4'}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                await asyncio.to_thread(ydl.download, [message.text])
            await message.answer_video(types.FSInputFile("video.mp4"), caption="✅ Tayyor!")
            await status.delete()
            if os.path.exists("video.mp4"): os.remove("video.mp4")
        except Exception:
            await status.edit_text("❌ Xatolik yuz berdi.")

    # QIDIRUV BO'LSA
    elif message.text:
        status = await message.answer("🔍 Qidirilmoqda...")
        results = await search_music(message.text)
        if not results:
            await status.edit_text("❌ Topilmadi.")
            return
        text = "🎵 **Topilgan qo'shiqlar:**\n\n"
        row_buttons = []
        for i, entry in enumerate(results, 1):
            text += f"{i}. {entry['title']}\n"
            row_buttons.append(InlineKeyboardButton(text=str(i), callback_data=f"music_{entry['id']}"))
        await status.delete()
        await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[row_buttons]))

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
