import aiohttp
import asyncio
import re

from pymongo import MongoClient

from aiogram import Router
from aiogram.types import Message
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.formatting import *

from states.classes import PinterestStates
from parser_files.functions import (
    work,
    extract_query_and_time
)


router = Router()
client = MongoClient()
db = client['pinterest']
collection = db['users']

@router.message(Command('start'))
async def start(message: Message):
    await message.answer(
        **as_list(
            Text("Привет, ", Bold(message.from_user.full_name), '!'),
            Text("Я бот, который может присылать пины из Pinterest через определенный промежуток времени!"),
            Text("На данный момент, отслеживать можно только один пин, но в дальнейшем, если я буду полезен, это исправится."),
            Text("Чтобы начать, достаточно отправить мне команду ", BotCommand('/add'), '.'),
            Text("Чтобы удалить отслеживаемый запрос, можно воспользоваться командой ", BotCommand('/cancel'), '.'),
            'Внизу есть меню с доступными командами. Это удобно. Пользуйся.',
            Bold('Начнем?'),
            sep='\n\n'
        ).as_kwargs()
    )

@router.message(Command('add'))
async def add(message: Message, state: FSMContext):
    user = message.from_user
    id = user.id
    if collection.find_one({'id' : id}):
        pass
    else:
        collection.insert_one({
            'id' : id,
            'fullname' : user.full_name
        })
    data = await state.get_data()
    if data:
        await message.answer('У вас уже установлен pin для отслеживания.')
        return 
    await state.set_state(PinterestStates.ask_query)
    await message.answer(
        **as_list(
            Text('Отлично, введите название pin`a для отслеживания и интервал в формате ', Bold('HH:MM:SS')),
            Text("Например, вы можете написать так: ", Bold("корги 00:15:00.")),
            "Это значит, что я буду отслеживать для вас пины, связанные с корги и присылать их каждые 15 минут.",
            Text(Bold('Часы'), ' могут принимать значение ', Underline('от 00 до 23'), ', а ', Bold('минуты с секундами от 00 до 59'), ' соответственно.'),
            "Если не указать время, по умолчанию интервал будет равен 15 минутам.",
            "Также нельзя установить интервал меньше 30 секунд.",
            sep='\n\n'
        ).as_kwargs(),
    )


@router.message(PinterestStates.ask_query)
async def get_query(message: Message, state: FSMContext, session: aiohttp.ClientSession):
    result_extract = await extract_query_and_time(message.text)
    if result_extract is None:
        await message.answer('Неверный формат введенного интервала. Попробуйте снова.')
        return 
    
    time_object, query = result_extract
    if re.search(r'\w', query) is None:
        await message.answer('Запрос (aka pin) не должен быть пустым. Попробуйте снова.')
        return
    
    hours = time_object.hour
    minutes = time_object.minute
    seconds = time_object.second
    if hours == 0 and minutes == 0:
        if seconds < 30:
            await message.answer('Вы не можете поставить интервал меньше 30 секунд.')
            return
    
    await state.set_state(PinterestStates.process)
    user_time_in_seconds = 60 ** 2 * hours + 60 * minutes + seconds
    collection.update_one(
        {'id' : message.from_user.id},
        {'$set' : {
            'query' : query,
            'time' : user_time_in_seconds
        }}
    )
    task = asyncio.create_task(work(query, message, session, state, user_time_in_seconds))
    await state.set_data({"task" : task})
    await task

@router.message(Command('cancel'))
async def cancel_task(message: Message, state: FSMContext):
    data = await state.get_data()
    if data:
        task = data.pop('task')
        task.cancel()
        await message.answer(
            **as_list(
                'Я больше не отслеживаю для вас запрос.',
                "Вы можете установить новый pin для отслеживания через команду /add."
            ).as_kwargs()
        )
        collection.update_one(
            {'id' : message.from_user.id},
            {'$unset' : {'query' : ''}}
        )
    else:
        await message.answer('У вас нет отслеживаемых пинов.')
    await state.clear()
