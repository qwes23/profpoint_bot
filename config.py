# -*- coding: utf-8 -*-

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from db_manager import DatabaseManager

with open('admins.txt', "r") as file:
    admins = file.read().split("\n")

with open("config.txt", "r") as file:
    file_split = file.read().split("\n")
    bot_token = file_split[0].split("!")[1]

bot = Bot(token=bot_token, parse_mode="HTML")
storage = MemoryStorage()
base = DatabaseManager()

dp = Dispatcher(bot, storage=storage)
