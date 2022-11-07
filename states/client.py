from aiogram.dispatcher.filters.state import StatesGroup, State


class HelpFSM(StatesGroup):
    get_comment = State()
    get_answer = State()

class FSMregistration(StatesGroup):
    name = State()
    surname = State()
    email = State()
    phone = State()

class FSMassignation(StatesGroup):
    number = State()

class FSMgetnumberofcheck(StatesGroup):
    number = State()
