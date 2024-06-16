import os
import asyncio
import aiohttp
import re
import pymongo

from dotenv import load_dotenv

from main import get_results

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, URLInputFile, InputMediaPhoto
from aiogram.filters.command import Command
from aiogram.utils.formatting import *
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class Pins(StatesGroup):
    add = State()
    remove = State()
    t = State()

add_queue = asyncio.Queue()

load_dotenv()
bot_token = os.getenv('BOT_TOKEN')
dp = Dispatcher()

bot = Bot(bot_token)


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
async def add_pins(message: Message, state: FSMContext, session: aiohttp.ClientSession):
    query = message.text
    if query.startswith('/'):
        await message.answer('Название пина не может начинаться с /. Попробуйте снова.')
        return
    await state.set_state(Pins.t)
    user = message.from_user
    id = user.id
    find_user = collection.find_one({'id' : id})
    collection.update_one(
        {'id' : id},
        {'$set' : {**find_user, 'query' : query}}
    )
    db['querys'].insert_one({
        'id' : id,
        'query' : query
    })
    await message.answer('Отлично! Я добавил ваш запрос. Теперь укажите через какое время вы желаете получать пины (в минутах)')
    await message.answer(
        **as_list(
            Text(Bold('Например, '), 'вы можете указать следующие числа:'),
            as_key_value(
                Underline(1440),
                'Интервал равный одному дню.'
            ),
            as_key_value(
                Underline(60),
                'Интервал равный одному часу.'
            ),
            as_key_value(
                Underline(1),
                'Интервал равный одной минуте.'
            ),
            as_key_value(
                Underline(0.5),
                'Интервал равный 30 секундам.'
            ),
            Text("Стоит заметить, что интервал ", Bold("меньше, чем 30 секунд ставить нельзя. "), "Это сделано из соображений спама.")
        ).as_kwargs()
    )
    # task = asyncio.create_task(
    #     coro=send_group(session, query, id),
    #     name=str(id)
    # )
    # await task

@dp.message(Command('cancel'))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Я почистил историю. Теперь вы можете начать заново.')

@dp.message(Pins.t)
async def set_time(message: Message, session: aiohttp.ClientSession, state: FSMContext):
    t = message.text
    try:
        t = float(t.replace(',', '.'))
    except:
        await message.answer('Нужно указать просто число. Попробуйте еще раз. Например, 15.')
        return
    if t < 0.5:
        await message.answer('Нельзя поставить интервал меньше 30 секунд. Попробуйте снова.')
        return
    await state.clear()
    user = message.from_user
    id = user.id
    find_user = collection.find_one({'id' : id})
    collection.update_one(
        {'id' : id},
        {'$set' : {**find_user, 'time' : t}}
    )
    query = find_user['query']
    await message.answer('Отлично! Я добавил ваш запрос и время. Вы будете получать пины каждые {} минут.'.format(t))
    task = asyncio.create_task(
        coro=send_group(session, query, id, t),
        name=str(id)
    )
    await task
    

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
            {'$unset' : {'query' : '', 'time' : ''}}
        )
    for task in asyncio.all_tasks():
        if task.get_name() == str(id):
            task.cancel()
    await message.answer('Отлично! Я удалил ваш запрос. Теперь вы можете добавить новый.')
    

@dp.message(Command('list'))
async def get_querys(message: Message):
    user = message.from_user
    id = user.id
    db_user = collection.find_one({'id' : id})
    if 'query' in db_user:
        await message.answer(**Text("Я отслеживаю для вас запрос ", Bold(db_user['query'])).as_kwargs())
    else:
        await message.answer('У вас нет запросов для отслеживания')
 
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
            ),
            as_key_value(
                BotCommand('/list'),
                'Посмотреть список отслеживаемых пинов'
            ),
            as_key_value(
                BotCommand('/cancel'),
                "Начать заново"
            ),
            as_key_value(
                BotCommand('/time'),
                'Узнать интервал в минутах между пинами.'
            ),
            as_key_value(
                BotCommand('/help'),
                'FAQ'
            )
        ).as_kwargs()
    )

@dp.message(Command('help'))
async def help(message: Message):
    await message.answer(
        **as_list(
            Bold('Ответы на частые вопросы:'),
            as_key_value(
                'Не приходят пины',
                'Скорее всего дело в том, что запрос, который вы ввели не имеет права на существование на Pinterest. То есть, вводя его на сайте или в приложении, вы получите пустую выдачу. Такое бывает.'
            ),
            as_key_value(
                'Как поменять интервал?',
                'Чтобы поменять интервал, стоит удалить текущий запрос, затем снова добавить с учетом пожеланий касаемо интервала. В дальнейшем эта проблема будет исправлена.'
            ),
            as_key_value(
                'Каков фундамент бота?',
                Text('Бот написан на ', Bold('Python'), ' с использованием фреймворка ', Bold('aiogram'), '.')
            ),
            as_key_value(
                'Как отключить бота?',
                Text('Достаточно написать ', BotCommand('/remove'), ' чтобы удалить все отслеживаемые запросы и не получать уведомлений.')
            ),
            Text(
                'Бот находится в стадии разработки. Если вы заинтересованы в дальнейшей разработке и улучшении данного бота, напишите об этом через ',
                BotCommand('/contacts'), ' .',
            ),
        ).as_kwargs()
    )
    await message.answer(
        **as_marked_section(
            Italic('В планах:'),
            'Добавить большее количество запросов.',
            'Добавить поддержку просмотра видео.',
            marker='🔑 '
        ).as_kwargs()
    )

@dp.message(Command('time'))
async def get_time(message: Message):
    user = message.from_user
    id = user.id
    db_user = collection.find_one({'id' : id})
    if db_user is None:
        await message.answer('Вы ни разу не добавляли запрос для отслеживания. Сделайте это через /add')
        return 
    else:
        if 'time' in db_user:
            await message.answer('{} - интервал в минутах между пинами.'.format(db_user['time']))
            return
        else:
            await message.answer('Вы не установили время.')
            return 

async def send_group(session: aiohttp.ClientSession, query: str, id: int, time: float):
    group = []
    try:
        async for url in get_results(session, query):
            try:
                if len(group) == 10:
                    await bot.send_media_group(
                        id,
                        group
                    )
                    group.clear()
                    await asyncio.sleep(60 * time)
                image = InputMediaPhoto(media=URLInputFile(url))
                group.append(image)
            except Exception as e:
                db['errors'].insert_one({'message' : str(e)})
    except asyncio.CancelledError:
        pass
    except Exception as e:
        db['errors'].insert_one({'message' : str(e)})



async def run(session: aiohttp.ClientSession):
    users = [user for user in collection.find({'$and' : [{'query' : {'$exists' : True}}, {'time' : {'$exists' : True}}]})]
    tasks = []
    for user in users:
        id = user['id']
        await bot.send_message(id, 'Я прекращал свою работу для устранения неполадок. Теперь вроде работает, ожидайте пины!')
        query = user['query']
        t = user['time']
        tasks.append(
            asyncio.create_task(
                coro=send_group(session, query, id, t),
                name=str(id)
            )
        )
    await asyncio.gather(*tasks)

async def main():
    async with aiohttp.ClientSession() as session:
        await asyncio.gather(
            run(session),
            dp.start_polling(bot, session=session)
        )

asyncio.run(main())
client.close()