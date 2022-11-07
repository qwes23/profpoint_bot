from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup

help_type_choose_kb = InlineKeyboardMarkup(row_width=1)
help_type_choose_kb.add(InlineKeyboardButton(text="Помощь в работе бота", callback_data="help_bot"))
help_type_choose_kb.add(InlineKeyboardButton(text="Помощь в оплате", callback_data="help_payment"))

async def get_help_answer_kb(userid):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(text="Ответить", callback_data=f"helpanswer_{userid}"))
    return keyboard
