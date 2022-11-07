from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add("📄Мои проверки")
main_kb.insert("📋Инструкция")
main_kb.add(KeyboardButton("🔎Проверки рядом со мной", request_location=True))
main_kb.add("🆘Помощь")
main_kb.insert("💸Оплата")

cancel_kb = InlineKeyboardMarkup(row_width=1)
cancel_kb.add(InlineKeyboardButton(text="Отмена", callback_data="cancel"))

check_kb = ReplyKeyboardMarkup(resize_keyboard=True)
check_kb.add("📎Назначить проверку")
check_kb.add("📙Вернуться в меню")

async def get_cancel_check_kb(check_id):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(text="Отменить проверку", callback_data=f"uncheck_{check_id}"))
    return keyboard

my_checks_kb = ReplyKeyboardMarkup(resize_keyboard=True)
my_checks_kb.add("📋Заполнить анкету")
my_checks_kb.add("📙Вернуться в меню")

grade_kb = InlineKeyboardMarkup(row_width=1)
grade_kb.add(InlineKeyboardButton(text="Выполнено", callback_data="grade_2"))
grade_kb.add(InlineKeyboardButton(text="Частично выполнено", callback_data="grade_1"))
grade_kb.add(InlineKeyboardButton(text="Не выполнено", callback_data="grade_0"))
grade_kb.add(InlineKeyboardButton(text="Невозможно оценить", callback_data="grade_N"))

grade31_kb = InlineKeyboardMarkup(row_width=1)
grade31_kb.add(InlineKeyboardButton(text="1 (Абсолютно недоволен)", callback_data="grade_1"))
grade31_kb.add(InlineKeyboardButton(text="2", callback_data="grade_2"))
grade31_kb.add(InlineKeyboardButton(text="3", callback_data="grade_3"))
grade31_kb.add(InlineKeyboardButton(text="4", callback_data="grade_4"))
grade31_kb.add(InlineKeyboardButton(text="5", callback_data="grade_5"))
friendliess_kb = InlineKeyboardMarkup(row_width=1)
friendliess_kb.add(InlineKeyboardButton(text="Да", callback_data="grade_1"))
friendliess_kb.add(InlineKeyboardButton(text="Нет", callback_data="grade_2"))

kastorama_kb = InlineKeyboardMarkup(row_width=1)
kastorama_kb.add(InlineKeyboardButton(text="Да", callback_data="grade_1"))
kastorama_kb.add(InlineKeyboardButton(text="Нет", callback_data="grade_0"))
