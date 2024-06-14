import os
import asyncio

from dotenv import load_dotenv


from pinterest_parser import PinterestParserImages
from aiogram import Bot, Dispatcher
from aiogram.types import Message, URLInputFile
from aiogram.filters.command import CommandStart

load_dotenv()

bot_token = os.getenv('BOT_TOKEN')

dp = Dispatcher()

parser = PinterestParserImages(seconds=60 * 15)

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer('Я буду присылать тебе мемы)')
    index_filename = 1
    async for url in parser.images_generator():
        image = URLInputFile(url, filename=f"picture_{index_filename}.jpeg")
        await message.answer_photo(image)
        index_filename += 1
        await asyncio.sleep(2)

async def main():
    bot = Bot(bot_token)
    await dp.start_polling(bot)

asyncio.run(main())