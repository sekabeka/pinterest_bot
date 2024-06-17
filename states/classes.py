from aiogram.fsm.state import State, StatesGroup

class PinterestStates(StatesGroup):
    ask_query = State()
    process = State()