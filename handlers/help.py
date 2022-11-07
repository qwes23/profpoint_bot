import asyncio

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from config import dp, bot, base, admins

from keyboards.admin import *
from states.client import *


@dp.message_handler(Text("🆘Помощь"))
async def get_help_choose_menu(message: types.Message):
    await message.answer("<b>🆘Выберите тип помощи</b>", reply_markup=help_type_choose_kb)


@dp.callback_query_handler(Text(startswith="help_"))
async def get_help_choose(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text("<b>Введите комментарий, который увидит наш менеджер</b>")
    await HelpFSM.get_comment.set()
    async with state.proxy() as data:
        data['message_id'] = call.message.message_id
        data['user_id'] = call.from_user.id
        data['help_type'] = call.data.split("_")[1]


@dp.message_handler(state=HelpFSM.get_comment)
async def get_help_comment(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['comment'] = message.text
        registration_data = await base.get_help_info(message.from_user.id)
        type_help_text = "Помощь в работе бота" if data['help_type'] == "bot" else "Помощь в оплате"
        for admin in admins:
            await bot.send_message(admin, f"<b>🔔Новый запрос на помощь!</b>\n\n"
                                          f"<b>👤Пользователь:</b> {registration_data[1]} {registration_data[2]}\n"
                                          f"<b>🆘Тип помощи: {type_help_text}</b>\n\n"
                                          f"<b>📄Комментарий пользователя: {data['comment']}</b>",
                                   reply_markup=await get_help_answer_kb(data['user_id']))
            await asyncio.sleep(0.2)
    await message.answer("<b>Мы спешим на помощь! Ожидайте ответа!</b>")
    await state.finish()

@dp.callback_query_handler(Text(startswith="helpanswer_"), user_id=admins)
async def answer_help_request(call: types.CallbackQuery, state: FSMContext):
    await HelpFSM.get_answer.set()
    async with state.proxy() as data:
        data['message_text'] = call.message.text
        data['message_id'] = call.message.message_id
        data['request_id'] = call.data.split("_")[1]
    await call.message.edit_text(call.message.text + "\n\n<b>✏Введите ответ</b>")

@dp.message_handler(state=HelpFSM.get_answer)
async def get_answer_text(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        await bot.send_message(data['request_id'], f"<b>🔔Ответ по вашему запросу о помощи</b>:\n\n"
                                                   f"{message.text}")
        await bot.edit_message_text(f"{data['message_text']}\n\n✔Отвечено", message.from_user.id, data['message_id'])
    await state.finish()
