import os
import asyncio
import aiohttp
import re
import pymongo

from dotenv import load_dotenv


from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, URLInputFile, InputMediaPhoto
from aiogram.filters.command import Command
from aiogram.utils.formatting import *
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class Pins(StatesGroup):
    add = State()
    remove = State()

load_dotenv()
bot_token = os.getenv('BOT_TOKEN')
dp = Dispatcher()

client = pymongo.MongoClient()
db = client['pinterest']
collection = db['users']


@dp.message(Command('add'))
async def add_user(message: Message, state: FSMContext):
    user = message.from_user
    id = user.id
    find_user = collection.find_one({'id' : id})
    if find_user is None:
        user_info = {
            'id' : id,
            'fullname' : user.full_name,
        }
        collection.insert_one(user_info)
    else:
        if 'query' in find_user:
            await message.answer('Пока что я могу отслеживать лишь один запрос. Удалите и добавьте новый, если в этом есть необходимость. Если Вы заинтересованы в развитии данного бота и добавления возможности отслеживать несколько запросов, напишите через обратную связь. Спасибо!')
            return 
    await state.set_state(Pins.add)
    await message.answer('Введите запрос, который я буду отслеживать.')

@dp.message(Pins.add)
async def add_pins(message: Message, state: FSMContext):
    await state.clear()
    query = message.text
    user = message.from_user
    id = user.id
    find_user = collection.find_one({'id' : id})
    collection.update_one(
        {'id' : id},
        {'$set' : {**find_user, 'query' : query}}
    )
    await message.answer('Отлично! Я добавил ваш запрос. Теперь вы будете получать новые пины каждые N минут')

@dp.message(Command('remove'))
async def remove(message: Message):
    user = message.from_user
    id = user.id
    find_user = collection.find_one({'id' : id})
    if find_user is None:
        await message.answer('Вы не добавляли ни одного запроса для отслеживания. Сделайте это через команду /add')
        return 
    else:
        if 'query' not in find_user:
            await message.answer('У вас нет отслеживаемых запросов. Установите новый через /add')
            return
        collection.update_one(
            {'id' : id},
            {'$unset' : {'query' : ''}}
        )
    await message.answer('Отлично! Я удалил ваш запрос. Теперь вы можете добавить новый.')
 
@dp.message(Command('contacts'))
async def contacts(message: Message):
    await message.answer(
        **as_list(
            Text('Обратная связь поможет мне развиваться. Спасибо!'),
            as_key_value(
                'Telegram',
                'https://t.me/photoarsenij'
            )
        ).as_kwargs()
    )

@dp.message(Command('start'))
async def start(message: Message):
    await message.answer(
        **as_list(
            Text('Привет, ', Bold(message.from_user.full_name), '!'),
            Text('Я бот, который может присылать тебе пины из Pinterest`a через определенное время.'),
            Text('Это может быть полезно многим. В частности, я могу присылать тебе каждые 15 минут мемы, чтобы отвлечься и разгрузить свой мозг. Техника Pomodoro.'),
            Text('Не забывай, что я также могу присылать тебе мотивационные фразы, чтобы не падать духом или референсы для съемок. Что угодно.'), 
        ).as_kwargs()
    )
    await message.answer(
        **as_list(
            Bold('Доступные команды'),
            as_key_value(
                BotCommand('/add'),
                'Добавить пин для отслеживания'
            ),
            as_key_value(
                BotCommand('/remove'),
                'Удалить пин из отслеживаемых'
            ),
            as_key_value(
                BotCommand('/contacts'),
                'Обратная связь'
            )
        ).as_kwargs()
    )

async def main():
    bot = Bot(bot_token)
    await dp.start_polling(bot)

asyncio.run(main())