import aiohttp
import asyncio
import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from handlers.main_handlers import router


load_dotenv()
bot_token = os.getenv('BOT_TOKEN')


async def main():
    dp = Dispatcher()
    dp.include_router(router)

    bot = Bot(bot_token)
    await bot.set_my_commands(
        commands=[
            BotCommand(
                command='run',
                description='добавить пин для отслеживания'
            ),
            BotCommand(
                command='cancel',
                description='отменить отслеживание пина'
            )
        ]
    )

    async with aiohttp.ClientSession() as session:
        await dp.start_polling(bot, session=session)

asyncio.run(main())