import asyncio

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from config import dp, bot, base, admins

from keyboards.client import *
from states.client import *

@dp.message_handler(state=FSMregistration.name)
async def getting_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['id'] = message.from_user.id
        data['name'] = message.text
    await FSMregistration.next()
    await message.answer('<b>Напишите свою фамилию</b>')
    await asyncio.sleep(300)
    if await state.get_state() == FSMregistration.surname and 'surname' not in (await state.get_data()).keys():
        await message.answer("Тук-тук, кажется вы прервались. Пожалуйста, продолжите регистрацию")

@dp.message_handler(state=FSMregistration.surname)
async def getting_surname(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['surname'] = message.text
    await FSMregistration.next()
    await message.answer('<b>Введите ваш EMAIL</b>')
    await asyncio.sleep(300)
    if await state.get_state() == FSMregistration.email and 'email' not in (await state.get_data()).keys():
        await message.answer("Тук-тук, кажется вы прервались. Пожалуйста, продолжите регистрацию")


@dp.message_handler(state=FSMregistration.email)
async def getting_email(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['email'] = message.text
    await message.answer("<b>Введите ваш номер телефона</b>")
    await FSMregistration.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMregistration.phone and 'phone' not in (await state.get_data()).keys():
        await message.answer("Тук-тук, кажется вы прервались. Пожалуйста, продолжите регистрацию")

@dp.message_handler(state=FSMregistration.phone)
async def getting_phone(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['phone'] = message.text
        data['telegram_name'] = message.from_user.full_name
    await base.add_user((await state.get_data()).values())
    await message.answer('<b>Спасибо! Теперь вы зарегистрированы</b>', reply_markup=main_kb)
    await state.finish()
