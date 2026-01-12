import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web
import yt_dlp

# 1. SOZLAMALAR
TOKEN = "8429904690:AAHYJsFVU4gkYQWNwYZyk-7M2zTFiYvmmMk"
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 2. KOYEB UCHUN PORT (Bot o'chib qolmasligi uchun)
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()

# 3. YORDAM PANELI (Inline Keyboard)
def help_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆘 Yordam", callback_data="help_info")],
        [InlineKeyboardButton(text="👨‍💻 Dasturchi", url="https://t.me/SizningLoginingiz")]
    ])
    return keyboard

# 4. START BUYRUQI
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "<b>Assalomu alaykum! ✨</b>\n\n"
        "Men Instagram-dan video yuklovchi botman! 📥\n"
        "Menga havola yuboring va men uni sizga yuboraman. 🚀",
        parse_mode="HTML",
        reply_markup=help_keyboard()
    )

# 5. INSTAGRAM YUKLOVCHI
@dp.message()
async def download_insta(message: types.Message):
    if "instagram.com" in message.text:
        wait_msg = await message.answer("🔄 <b>Iltimos kuting, video tayyorlanmoqda...</b>", parse_mode="HTML")
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'insta_video.mp4',
            'noplaylist': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([message.text])
            
            video = types.FSInputFile("insta_video.mp4")
            await message.answer_video(
                video, 
                caption="✅ <b>Video muvaffaqiyatli yuklandi!</b>\n\n@Instagram_Video_Bot 🚀", 
                parse_mode="HTML"
            )
            os.remove("insta_video.mp4")
        except Exception as e:
            await message.answer(f"❌ <b>Xatolik yuz berdi:</b> {str(e)}", parse_mode="HTML")
        finally:
            await wait_msg.delete()
    else:
        await message.answer("⚠️ <b>Iltimos, faqat Instagram havolasini yuboring!</b>", parse_mode="HTML")

# 6. CALLBACK (Tugma bosilganda yordam berish)
@dp.callback_query(lambda c: c.data == "help_info")
async def process_callback_help(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        "📌 <b>Yordam bo'limi:</b>\n\n"
        "1. Instagram-da videoni toping.\n"
        "2. Linkini (havola) nusxalang.\n"
        "3. Botga yuboring.\n"
        "4. Bir necha soniya kuting! ⏳",
        parse_mode="HTML"
    )

# 7. ISHGA TUSHIRISH
async def main():
    await start_web_server() # Koyeb uchun kerak
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
