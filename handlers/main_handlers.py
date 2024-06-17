import aiohttp
import asyncio
import re

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

@router.message(Command('run'))
async def run(message: Message, state: FSMContext):
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
            "Если не указать время, по умолчанию интервал будет равен 15 минутам.",
            "Также нельзя установить интервал меньше 30 секунд.",
            sep='\n\n'
        ).as_kwargs()
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
    if seconds < 30 and ((hours and minutes) == 0):
        await message.answer('Вы не можете поставить интервал меньше 30 секунд.')
        return
    
    await state.set_state(PinterestStates.process)

    task = asyncio.create_task(work(query, message, session, state, 60 ** 2 * hours + 60 * minutes + seconds))
    await state.set_data({"task" : task})
    await task

@router.message(Command('cancel'), PinterestStates.process)
async def cancel_task(message: Message, state: FSMContext):
    data = await state.get_data()
    task = data.pop('task')
    task.cancel()
    await message.answer(
        **as_list(
            'Я больше не отслеживаю для вас запрос.',
            "Вы можете установить новый pin для отслеживания через команду /run."
        ).as_kwargs()
    )
    await state.clear()