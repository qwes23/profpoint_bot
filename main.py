# -*- coding: utf-8 -*-

from config import dp, bot, admins
from aiogram import executor
from db_manager import DatabaseManager
import handlers, middlewares, keyboards, states

async def on_startup(_):
    await DatabaseManager().create_tables()
    print("Бот онлайн")

if __name__ == "__main__":
    middlewares.setup(dp)
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)