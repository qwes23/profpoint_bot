import asyncio

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from config import dp, bot, base, admins

from keyboards.client import *
from states.client import *

@dp.message_handler(Text(["📙Вернуться в меню", "/start"]), state="*")
async def start_message(message: types.Message, state: FSMContext):
    if await base.user_exists(message.from_user.id):
        await message.answer("<b>📒Главное меню</b>", reply_markup=main_kb)
    else:
        await message.answer("<b>Напишите свое имя</b>")
        await FSMregistration.name.set()
        await asyncio.sleep(300)
        if await state.get_state() == FSMregistration.name and 'name' not in (await state.get_data()).keys():
            await message.answer("Тук-тук, кажется вы прервались. Пожалуйста, продолжите регистрацию")


@dp.message_handler(Text("💸Оплата"))
async def payment_message(message: types.Message):
    await message.answer("""Оплата за все проверки прошлого месяца суммируется и начисляется к 15-му числу текущего месяца. Например, за все работы, которые вы выполнили в октябре, оплата будет начислена к 15-му ноября.

15-го числа каждого месяца Вам на почту приходит письмо, в котором указана заработанная сумма за прошлый месяц.

Оплата будет осуществляться трем категориям получателей:

«Самозанятый» на Qugo - дополнительный налог 6% уплачивается самостоятельно,

«Физическое лицо» на Solar Staff - оплата начисляется за вычетом 7%

ИП на Solar Staff – налог выплачивается самостоятельно в зависимости от системы налогооблажения ИП""")

@dp.callback_query_handler(Text("cancel"), state="*")
async def cancel_action(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.answer("<b>❌Действие отменено</b>")
    await call.message.delete()
