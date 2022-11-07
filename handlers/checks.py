import asyncio
from datetime import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from config import dp, bot, base, admins

from keyboards.client import *
from states.client import *
from states.forms import *

@dp.message_handler(content_types=['location'])
async def get_free_checks(message: types.Message, state: FSMContext):
    user_longitude = message.location.longitude
    user_latitude = message.location.latitude
    longitude1 = user_longitude - 3
    longitude2 = user_longitude + 3
    latitude1 = user_latitude - 3
    latitude2 = user_latitude + 3
    checks = await base.get_available_checks(latitude1, longitude1, latitude2, longitude2)
    names = {"mts": "Салон связи", "sokolov": "Ювелирный магазин", "gate31": "Магазин одежды", "irbis": "АЗС",
             "kastorama": "Гипермаркет товаров для дома и строительства", "muztorg": "Магазин музыкальных инструментов"}
    if len(checks):
        await message.answer("📌<b>Список доступных проверок рядом с вами</b>", reply_markup=check_kb)
        for check in checks:
            await message.answer(f"<b>📎Номер проверки:</b> <code>{check[0]}</code>\n"
                                 f"<b>📍Адрес:</b> {check[1]}\n"
                                 f"<b>🈚Тип:</b> {names[check[2]]}")
            await asyncio.sleep(0.2)
    else:
        await message.answer("<b>❌К сожалению, на данный момент проверки рядом с вами не найдены</b>")

@dp.message_handler(Text("📎Назначить проверку"))
async def appoint_check(message: types.Message, state: FSMContext):
    await message.answer("<b>🔢Введите номер проверки</b>", reply_markup=cancel_kb)
    await FSMassignation.number.set()

@dp.message_handler(state=FSMassignation.number)
async def get_appoint_number(message: types.Message, state: FSMContext):
    try:
        is_check_assignated = await base.assignate_check(message.from_user.id, int(message.text))
        if is_check_assignated:
            await message.answer(f"<b>✅Проверка под номером <code>{message.text}</code> успешно назначена</b>")
            await base.add_log(message.from_user.id, message.text, 'Назначил')
        else:
            await message.answer(f"<b>❌Проверка с таким номером не найдена или на неё назначен другой ТП</b>")
    except ValueError:
        await message.answer("<b>❌Ошибка: Номер проверки должен быть числом</b>")
    finally:
        await state.finish()

@dp.message_handler(Text("📄Мои проверки"))
async def get_user_checks(message: types.Message, state: FSMContext):
    user_checks = await base.get_user_checks(int(message.from_user.id))
    if len(user_checks):
        await message.answer("<b>📔Список ваших проверок:</b>", reply_markup=my_checks_kb)
        for check in user_checks:
            await message.answer(f"<b>📎Номер проверки:</b> <code>{check[0]}</code>\n"
                                 f"<b>📍Адрес:</b> {check[1]}\n", reply_markup=await get_cancel_check_kb(check[0]))
    else:
        await message.answer("<b>❌На данный момент у вас нет проверок</b>")

@dp.callback_query_handler(Text(startswith="uncheck_"))
async def cancel_check(call: types.CallbackQuery):
    check_id = call.data.split("_")[1]
    await base.cancel_check(check_id)
    await call.message.edit_text("✅Проверка отменена")
    await base.add_log(call.from_user.id, check_id, 'Отменил')

@dp.message_handler(Text("📋Заполнить анкету"))
async def fill_form(message: types.Message, state: FSMContext):
    await message.answer("<b>Напишите номер проверки</b>", reply_markup=cancel_kb)
    await FSMgetnumberofcheck.number.set()

@dp.message_handler(state=FSMgetnumberofcheck.number)
async def get_number_of_check_to_fill(message: types.Message, state: FSMContext):
    companies_states = {"mts": FSMmts.date, "sokolov": FSMsokolov.date, "gate31": FSMgate31.date, "irbis": FSMirbis.date, "muztorg": FSMmuztorg.date, "kastorama": FSMkastorama.date}
    try:
        company = await base.is_user_have_check(message.from_user.id, int(message.text))
        await companies_states[company].set()
        async with state.proxy() as data_check:
            data_check['company'] = company
            data_check['user_id'] = message.from_user.id
            data_check['number'] = int(message.text)
            data_check['date_time'] = datetime.now()
        await message.answer("<b>Введите дату проверки</b>")
        await asyncio.sleep(300)
        if 'date' not in (await state.get_data()).keys():
            await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")
    except ValueError:
        await message.answer("<b>❌Ошибка: Номер проверки должен быть числом!</b>")
        await state.finish()

@dp.message_handler(state=FSMsokolov.date)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['date'] = message.text
    await FSMsokolov.next()
    await message.answer('Время начала проверки. Формат 17:20')
    await asyncio.sleep(300)
    if await state.get_state() == FSMsokolov.time_start and 'time_start' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMsokolov.time_start)
async def getting_time_start(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['time_start'] = message.text
    await FSMsokolov.next()
    await message.answer('Пришлите аудиозапись визита')
    await asyncio.sleep(300)
    if await state.get_state() == FSMsokolov.audio and 'audio' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMsokolov.audio, content_types=types.ContentType.AUDIO)
async def getting_audio(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['audio'] = message.audio.file_id
    await FSMsokolov.next()
    await message.answer('ФИО сотрудника (Или описание внешности, если не удалось разглядеть бейдж)')
    await asyncio.sleep(300)
    if await state.get_state() == FSMsokolov.name_worker and 'worker_name' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMsokolov.name_worker)
async def getting_fio(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['worker_name'] = message.text
    await FSMsokolov.next()
    await message.answer("Точное количество продавцов в торговом зале в момент входа в магазин")
    await asyncio.sleep(300)
    if await state.get_state() == FSMsokolov.number_workers and 'worker_count' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMsokolov.number_workers)
async def getting_worker_count(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['worker_count'] = message.text
    await FSMsokolov.next()
    await message.answer("Количество посетителей (клиентов магазина) в торговом зале в момент входа в магазин")
    await asyncio.sleep(300)
    if await state.get_state() == FSMsokolov.number_clients and 'client_count' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMsokolov.number_clients)
async def getting_client_count(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['client_count'] = message.text
        data_check['edit_message_id'] = \
            (await message.answer("На момент посещения все сотрудники не заняты личными делами (не занимаются своим макияжем и не употребляют пищу)",
                                  reply_markup=grade_kb)).message_id
    await FSMsokolov.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMsokolov.worker_job and 'worker_job' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMsokolov.worker_job)
async def getting_worker_job(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['worker_job'] = call.data.split("_")[1]
        await call.message.edit_text("При обслуживании покупателей сотрудник использует специальную подложку для демонстрации ювелирных изделий", reply_markup=grade_kb)
    await FSMsokolov.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMsokolov.worker_substrate and 'worker_substrate' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMsokolov.worker_substrate)
async def getting_worker_substrate(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['worker_substrate'] = call.data.split("_")[1]
        await call.message.edit_text("Продавец был вовлечен в процесс обслуживания, хотел помочь, располагал к себе, "
                                     "демонстрировал доброжелательность, улыбался. Подробно расскажите о своих впечатлениях", reply_markup=grade_kb)
    await FSMsokolov.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMsokolov.worker_friendliness and 'worker_friendliness' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMsokolov.worker_friendliness)
async def getting_worker_friendliness(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['worker_friendliness'] = call.data.split("_")[1]
        await call.message.edit_text("По итогам визита сложилось впечатление гостеприимной атмосферы и высококлассного обслуживания. Подробно расскажите о своих впечатлениях", reply_markup=grade_kb)
    await FSMsokolov.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMsokolov.worker_service and 'worker_service' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMsokolov.worker_service)
async def getting_worker_service(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['worker_service'] = call.data.split("_")[1]
        await base.add_log(call.from_user.id, data_check['number'], 'Выполнил')
        await call.message.edit_text(f"Спасибо! Анкета {data_check['number']} - заполнена!")
    await base.add_check("sokolov", state)
    await state.finish()


@dp.message_handler(content_types=[types.ContentType.TEXT, types.ContentType.PHOTO], state=FSMsokolov.audio)
async def audio_loop(message: types.Message, state: FSMContext):
    message_id = (await message.answer("Неверный формат сообщения.\n\nПожалуйста, пришлите аудио")).message_id
    await asyncio.sleep(5)
    await bot.delete_message(message.from_user.id, message_id)

@dp.message_handler(state=FSMmts.date)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['date'] = message.text
    await FSMmts.next()
    await message.answer('Время начала проверки. Формат 17:20')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmts.time_start and 'time_start' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmts.time_start)
async def getting_time_start(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['time_start'] = message.text
    await FSMmts.next()
    await message.answer('Салон работал согласно режиму работы?')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmts.rezgim and 'rezgim' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmts.rezgim)
async def getting_rezgim(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['rezgim'] = message.text
    await FSMmts.next()
    await message.answer('Пришлите количество сотрудников, присутсвовавших во время визита')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmts.number_workers and 'number_workers' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmts.number_workers)
async def getting_number_workers(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['number_workers'] = int(message.text)
    await FSMmts.next()
    await message.answer('Пришлите количество клиентов, присутсвовавших во время визита')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmts.number_clients and 'number_clients' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmts.number_clients)
async def getting_number_clients(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['number_clients'] = int(message.text)
    await FSMmts.next()
    await message.answer(
        'Пришлите Имя и Должность сотрудника, который проводил консультацию. Если не помните - напишите: не помню. Формат: Иванов Иван Иванович, консультант')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmts.name_worker and 'name_worker' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmts.name_worker)
async def getting_name_worker(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['name_worker'] = message.text
    await FSMmts.next()
    await message.answer('Коротко опишите внешний вид сотрудника.')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmts.describe_worker and 'describe_worker' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmts.describe_worker)
async def getting_describe_worker(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['describe_worker'] = message.text
    await FSMmts.next()
    await message.answer('Напишите короткое резюме визита. Добавьте комментарии по желанию.')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmts.resume and 'resume' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmts.resume)
async def getting_resume(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['resume'] = message.text
    await FSMmts.next()
    await message.answer('Пришилите аудиозапись визита.')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmts.audio and 'audio' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmts.audio, content_types=types.ContentType.AUDIO)
async def getting_audio(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['audio'] = message.audio.file_id
    await FSMmts.next()
    await message.answer('Прикрепите фото фасада с первого ракурса.')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmts.photo1 and 'photo1' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmts.photo1, content_types=types.ContentType.PHOTO)
async def getting_photo1(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['photo1'] = f'https://api.telegram.org/file/bot5794915534:AAHb-BgGHR5eE3szwUsNYuyPKQ1x4CJaZBY/{(await bot.get_file(message.photo[-1].file_id))["file_path"]}'
    await FSMmts.next()
    await message.answer('Прикрепите фото фасада со второго ракурса.')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmts.photo2 and 'photo2' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmts.photo2, content_types=types.ContentType.PHOTO)
async def getting_photo2(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['photo2'] = f'https://api.telegram.org/file/bot5794915534:AAHb-BgGHR5eE3szwUsNYuyPKQ1x4CJaZBY/{(await bot.get_file(message.photo[-1].file_id))["file_path"]}'
        await base.add_log(message.from_user.id, data_check['number'], 'Выполнил')
    await base.add_check("mts", state)
    await message.answer(f'Спасибо! Анкета {data_check["number"]} -- заполнена!', reply_markup=main_kb)
    await state.finish()

@dp.message_handler(content_types=[types.ContentType.TEXT, types.ContentType.PHOTO], state=[FSMmts.photo2, FSMmts.photo1])
async def photo_loop(message: types.Message, state: FSMContext):
    message_id = (await message.answer("Неверный формат сообщения.\n\nПожалуйста, пришлите фото")).message_id
    await asyncio.sleep(5)
    await bot.delete_message(message.from_user.id, message_id)

@dp.message_handler(content_types=[types.ContentType.TEXT, types.ContentType.PHOTO], state=FSMmts.audio)
async def audio_loop(message: types.Message, state: FSMContext):
    message_id = (await message.answer("Неверный формат сообщения.\n\nПожалуйста, пришлите аудио")).message_id
    await asyncio.sleep(5)
    await bot.delete_message(message.from_user.id, message_id)

@dp.message_handler(state=FSMgate31.date)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['date'] = message.text
    await FSMgate31.next()
    await message.answer('Пришлите аудиозапись визита')
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.audio and 'audio' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMgate31.audio, content_types=types.ContentType.AUDIO)
async def getting_audio(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['audio'] = message.audio.file_id
    await FSMgate31.next()
    await message.answer('Пришлите фото фасада')
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.photo and 'photo' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMgate31.photo, content_types=types.ContentType.PHOTO)
async def getting_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['photo'] = f'https://api.telegram.org/file/bot5794915534:AAHb-BgGHR5eE3szwUsNYuyPKQ1x4CJaZBY/{(await bot.get_file(message.photo[-1].file_id))["file_path"]}'
    await FSMgate31.next()
    await message.answer("ФИО консультанта (Или описание внешности, если не удалось разглядеть бейдж)")
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.operator_name and 'operator_name' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMgate31.operator_name)
async def getting_operator_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['operator_name'] = message.text
    await FSMgate31.next()
    await message.answer("Оцените внешнее оформление: вывеску, входную группу, витрины, манекены, чистоту. Пожалуйста, опишите подробно, особенно если есть замечания")
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.outside and 'outside' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMgate31.outside)
async def getting_outside(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['outside'] = message.text
    await FSMgate31.next()
    await message.answer("Оцените внутреннее оформление: Торговый зал, примерочные, освещение, чистоту. Пожалуйста, опишите подробно, особенно если есть замечания")
    if await state.get_state() == FSMgate31.inside and 'inside' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMgate31.inside)
async def getting_inside(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['inside'] = message.text
    await FSMgate31.next()
    await message.answer("Оцените внешний вид и поведение сотрудников. Пожалуйста, опишите подробно, особенно если есть замечания")
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.describe_worker and 'describe_worker' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMgate31.describe_worker)
async def getting_describe_worker(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['describe_worker'] = message.text
    await message.answer("Товар имеет опрятный вид, имеются магнитные датчики безопасности")
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.product_appearance and 'product_appearance' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMgate31.product_appearance)
async def getting_product_appearance(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['product_appearance'] = message.text
        await message.answer("В примерочной присутствует ложка для обуви и вешалка", reply_markup=grade_kb)
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.spoon and 'spoon' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMgate31.spoon)
async def getting_spoon(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['spoon'] = message.text
        await message.answer("Укажите количество сотрудников в торговом зале")
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.worker_count and 'worker_count' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMgate31.worker_count)
async def getting_worker_count(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['worker_count'] = message.text
        await message.answer("Укажите количество покупателей в торговом зале")
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.client_count and 'client_count' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMgate31.client_count)
async def getting_client_count(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['client_count'] = message.text
        await message.answer("Консультант поприветствовал Вас с улыбкой", reply_markup=friendliess_kb)
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.consultant_friendliess and 'consultant_friendliess' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMgate31.consultant_friendliess)
async def getting_consultant_friendliess(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['consultant_friendliess'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer("Консультант проводил до примерочной ", reply_markup=friendliess_kb)
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.consultant_fitting and 'consultant_fitting' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMgate31.consultant_fitting)
async def getting_consultant_fitting(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['consultant_fitting'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer("Консультант сам отнес выбранные товары в примерочную", reply_markup=friendliess_kb)
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.consultant_products and 'consultant_products' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMgate31.consultant_products)
async def getting_consultant_products(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['consultant_products'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer("Консультант провел к кассовой зоне", reply_markup=friendliess_kb)
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.consultant_cash and 'consultant_cash' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMgate31.consultant_cash)
async def getting_consultant_cash(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['consultant_cash'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer('Консультант дождался оплаты (для универмага "Цветной", ТРЦ "Авиапарк", ТЦ "МЕГА Теплый стан")', reply_markup=friendliess_kb)
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.consultant_payment and 'consultant_payment' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMgate31.consultant_payment)
async def getting_consultant_payment(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['consultant_payment'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer('В примерочной обслуживал тот же сотрудник, что проводил консультацию в торговом зале', reply_markup=friendliess_kb)
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.consultant_same and 'consultant_same' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMgate31.consultant_same)
async def getting_consultant_same(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['consultant_same'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer("Имя дежурного по примерочной ")
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.duty_name and 'duty_name' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMgate31.duty_name)
async def getting_duty_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['duty_name'] = message.text
        await message.answer("Консультант/дежурный по примерочной проверил количество выбранных вещей до и после примерки", reply_markup=friendliess_kb)
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.consultant_product_count and 'consultant_product_count' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMgate31.consultant_product_count)
async def getting_consultant_product_count(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['consultant_product_count'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer('Консультант/дежурный по примерочной находился в непосредственной близости от примерочной', reply_markup=friendliess_kb)
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.consultant_closeness and 'consultant_closeness' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMgate31.consultant_closeness)
async def getting_consultant_closeness(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['consultant_closeness'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer('ФИО кассира (Или описание внешности, если не удалось разглядеть бейдж)')
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.cashier_name and 'cashier_name' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMgate31.cashier_name)
async def getting_cashier_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['cashier_name'] = message.text
        await message.answer("Кассир поприветствовал Вас с улыбкой", reply_markup=friendliess_kb)
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.cashier_friendliess and 'cashier_friendliess' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMgate31.consultant_friendliess)
async def getting_cashier_friendliess(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['cashier_friendliess'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer('Кассир/консультант завернул покупку в кальку (упаковочную бумагу) и положил в пакет', reply_markup=friendliess_kb)
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.cashier_paper and 'cashier_paper' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMgate31.cashier_paper)
async def getting_cashier_paper(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['cashier_paper'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer('Кассир/консультант передал пакет в руки, выйдя из-за кассы (не через кассовую стойку)', reply_markup=friendliess_kb)
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.cashier_handed and 'cashier_handed' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMgate31.cashier_handed)
async def getting_cashier_handed(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['cashier_handed'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer('Оцените общее впечатление от посещения магазина', reply_markup=grade_kb)
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.general_impression and 'general_impression' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMgate31.general_impression)
async def getting_general_impression(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['general_impression'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer('Оцените доброжелательность сотрудников', reply_markup=grade_kb)
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.worker_friendliess and 'worker_friendliess' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMgate31.worker_friendliess)
async def getting_worker_friendliess(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['worker_friendliess'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer('Оцените активность и заинтересованность консультирующего сотрудника', reply_markup=grade_kb)
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.consultant_activity and 'consultant_activity' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMgate31.consultant_activity)
async def getting_consultant_activity(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['consultant_activity'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer('Оцените компетентность консультирующего сотрудника', reply_markup=grade_kb)
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.worker_competence and 'worker_competence' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMgate31.worker_competence)
async def getting_worker_competence(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['worker_competence'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer('Оцените настойчивость консультанта в предложении продукции', reply_markup=grade_kb)
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.worker_persistence and 'worker_persistence' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMgate31.worker_persistence)
async def getting_worker_persistence(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['worker_persistence'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer('Оцените достаточно ли времени сотрудники уделили консультации и оформлению покупки', reply_markup=grade_kb)
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.worker_time and 'worker_time' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMgate31.worker_time)
async def getting_worker_time(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['worker_time'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer('Если ли желание вернуться в магазин и совершить еще покупки?', reply_markup=friendliess_kb)
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.return_desire and 'return_desire' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMgate31.return_desire)
async def getting_return_desire(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['return_desire'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer('ФИО сотрудника, проводившего возврат (Или описание внешности, если не удалось разглядеть бейдж)')
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.back_name and 'back_name' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMgate31.back_name)
async def getting_back_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['back_name'] = message.text
        await message.answer("Сотрудник поприветствовал Вас с улыбкой", reply_markup=friendliess_kb)
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.back_friendliess and 'back_friendliess' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMgate31.back_friendliess)
async def getting_back_friendliess(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['back_friendliess'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer('Оцените общее впечатление от возврата')
    await FSMgate31.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMgate31.back_main and 'back_main' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMgate31.back_main)
async def getting_back_main(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['back_main'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer(f"Спасибо! Анкета {data_check['number']} - заполнена!")
        await base.add_log(call.from_user.id, data_check['number'], 'Выполнил')
    await base.add_check("gate31", state)
    await state.finish()

@dp.message_handler(state=FSMgate31.photo, content_types=[types.ContentType.TEXT, types.ContentType.AUDIO])
async def photo_loop(message: types.Message, state: FSMContext):
    message_id = (await message.answer("Неверный формат сообщения.\n\nПожалуйста, пришлите фото")).message_id
    await asyncio.sleep(5)
    await bot.delete_message(message.from_user.id, message_id)

@dp.message_handler(state=FSMgate31.photo, content_types=[types.ContentType.TEXT, types.ContentType.PHOTO])
async def audio_loop(message: types.Message, state: FSMContext):
    message_id = (await message.answer("Неверный формат сообщения.\n\nПожалуйста, пришлите аудио")).message_id
    await asyncio.sleep(5)
    await bot.delete_message(message.from_user.id, message_id)

@dp.message_handler(state=FSMirbis.date)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['date'] = message.text
    await FSMirbis.next()
    await message.answer('Пришлите аудиозапись визита')
    await asyncio.sleep(300)
    if await state.get_state() == FSMirbis.audio and 'audio' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMirbis.audio, content_types=types.ContentType.AUDIO)
async def getting_audio(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['audio'] = message.audio.file_id
    await FSMirbis.next()
    await message.answer('Пришлите фото фасада')
    await asyncio.sleep(300)
    if await state.get_state() == FSMirbis.photo and 'photo' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMirbis.photo)
async def getting_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['photo'] = f'https://api.telegram.org/file/bot5794915534:AAHb-BgGHR5eE3szwUsNYuyPKQ1x4CJaZBY/{(await bot.get_file(message.photo[-1].file_id))["file_path"]}'
    await FSMirbis.next()
    await message.answer("Имя оператора АЗС (Или описание внешности, если не удалось разглядеть бейдж)")
    await asyncio.sleep(300)
    if await state.get_state() == FSMirbis.operator_name and 'operator_name' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMirbis.operator_name)
async def getting_operator_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['operator_name'] = message.text
    await FSMirbis.next()
    await message.answer("Имя заправщика АЗС (Или описание внешности, если не удалось разглядеть бейдж)")
    await asyncio.sleep(300)
    if await state.get_state() == FSMirbis.azs_name and 'azs_name' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMirbis.azs_name)
async def getting_azs_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['azs_name'] = message.text
    await FSMirbis.next()
    await message.answer("Номер колонки")
    if await state.get_state() == FSMirbis.column and 'column' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMirbis.column)
async def getting_column(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['column'] = message.text
    await FSMirbis.next()
    await message.answer("Оцените территорию АЗС и торговый зал. Везде ли было чисто, всё ли исправно. Пожалуйста, опишите подробно, особенно если есть замечания")
    await asyncio.sleep(300)
    if await state.get_state() == FSMirbis.territory and 'territory' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMirbis.territory)
async def getting_territory(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['territory'] = message.text
    await message.answer("Туалет чистый, в туалете хороший запах, график уборни заполнен. Пожалуйста, опишите подробно, особенно если есть замечания")
    await FSMirbis.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMirbis.sanuzel and 'sanuzel' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMirbis.sanuzel)
async def getting_sanuzel(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['sanuzel'] = message.text
        await message.answer("Насколько Вы довольны обстановкой на объекте?", reply_markup=grade_kb)
    await FSMirbis.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMirbis.situation and 'situation' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMirbis.situation)
async def getting_situation(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['situation'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer("Что бы Вы порекомендовали улучшить в обстановке на объекте?")
    await FSMirbis.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMirbis.object_tips and 'object_tips' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMirbis.object_tips)
async def getting_object_tips(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['object_tips'] = message.text
        await message.answer("Как Вы считаете, с какой проблемой обстановки на объекте компании нужно начать работать уже сейчас?")
    await FSMirbis.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMirbis.main_problem and 'main_problem' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMirbis.main_problem)
async def getting_main_problem(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['main_problem'] = message.text
        await message.answer("Оцените внешний вид и работу заправщика. Пожалуйста, опишите подробно, особенно если есть замечания")
    await FSMirbis.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMirbis.filler_job and 'filler_job' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMirbis.filler_job)
async def getting_filler_job(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['filler_job'] = message.text
        await message.answer("Насколько Вы довольны этапом заправки автомобиля?", reply_markup=grade_kb)
    await FSMirbis.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMirbis.fill and 'fill' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMirbis.fill)
async def getting_fill(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['fill'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer("Что бы Вы порекомендовали улучшить при заправке автомобиля?")
    await FSMirbis.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMirbis.fill_tips and 'fill_tips' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMirbis.fill_tips)
async def getting_fill_tips(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['fill_tips'] = message.text
        await message.answer("Как Вы считаете, с какой проблемой на этапе заправки автомобиля компании нужно начать работать уже сейчас? ")
    await FSMirbis.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMirbis.fill_problem and 'fill_problem' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMirbis.fill_problem)
async def getting_fill_problem(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['fill_problem'] = message.text
        await message.answer("Оцените внешний вид и работу оператора-кассира. Пожалуйста, опишите подробно, особенно если есть замечания")
    await FSMirbis.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMirbis.cashier_appearance and 'cashier_appearance' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMirbis.cashier_appearance)
async def getting_cashier_appearance(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['cashier_appearance'] = message.text
        await message.answer("Насколько Вы довольны работой оператора-кассира?", reply_markup=grade_kb)
    await FSMirbis.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMirbis.cashier_job and 'cashier_job' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMirbis.cashier_job)
async def getting_cashier_job(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['cashier_job'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer("Что бы Вы порекомендовали улучшить в работе оператора-кассира?")
    await FSMirbis.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMirbis.cashier_tips and 'cashier_tips' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMirbis.cashier_tips)
async def getting_cashier_tips(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['cashier_tips'] = message.text
        await message.answer("Как Вы считаете, с какой проблемой работы оператора-кассира компании нужно начать работать уже сейчас?")
    await FSMirbis.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMirbis.cashier_problem and 'cashies_problem' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMirbis.cashier_problem)
async def getting_cashier_problem(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['cashier_problem'] = message.text
        await message.answer(f"Спасибо! Анкета {data_check['number']} - заполнена!")
        await base.add_log(message.from_user.id, data_check['number'], 'Назначил')
    await base.add_check("irbis", state)
    await state.finish()

@dp.message_handler(state=FSMirbis.photo, content_types=[types.ContentType.AUDIO, types.ContentType.TEXT])
async def photo_loop(message: types.Message, state: FSMContext):
    message_id = (await message.answer("Неверный формат сообщения.\n\nПожалуйста, пришлите фото")).message_id
    await asyncio.sleep(5)
    await bot.delete_message(message.from_user.id, message_id)

@dp.message_handler(state=FSMirbis.photo, content_types=[types.ContentType.PHOTO, types.ContentType.TEXT])
async def audio_loop(message: types.Message, state: FSMContext):
    message_id = (await message.answer("Неверный формат сообщения.\n\nПожалуйста, пришлите аудио")).message_id
    await asyncio.sleep(5)
    await bot.delete_message(message.from_user.id, message_id)

@dp.message_handler(state=FSMmuztorg.date)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['date'] = message.text
    await FSMmuztorg.next()
    await message.answer('Время начала проверки. Формат 17:20')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmuztorg.audio and 'audio' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmuztorg.audio, content_types=types.ContentType.AUDIO)
async def getting_audio(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['audio'] = message.audio.file_id
    await FSMmuztorg.next()
    await message.answer('Пришлите фотографию фасада магазина')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmuztorg.photo1 and 'photo1' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmuztorg.photo1, content_types=types.ContentType.PHOTO)
async def getting_photo1(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['photo1'] = f'https://api.telegram.org/file/bot5794915534:AAHb-BgGHR5eE3szwUsNYuyPKQ1x4CJaZBY/{(await bot.get_file(message.photo[-1].file_id))["file_path"]}'
    await FSMmuztorg.next()
    await message.answer('Прикрепите фотографию нарушений')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmuztorg.photo2 and 'photo2' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmuztorg.photo2, content_types=types.ContentType.PHOTO)
async def getting_photo1(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['photo2'] = f'https://api.telegram.org/file/bot5794915534:AAHb-BgGHR5eE3szwUsNYuyPKQ1x4CJaZBY/{(await bot.get_file(message.photo[-1].file_id))["file_path"]}'
    await FSMmuztorg.next()
    await message.answer('Пришлите количество продавцов в магазине')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmuztorg.worker_count and 'worker_count' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmuztorg.worker_count)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['worker_count'] = message.text
    await FSMmuztorg.next()
    await message.answer('Пришлите количество клиентов в зале')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmuztorg.client_count and 'client_count' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmuztorg.client_count)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['client_count'] = message.text
    await FSMmuztorg.next()
    await message.answer('Напишите ваш пол')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmuztorg.sex and 'sex' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmuztorg.sex)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['sex'] = message.text
    await FSMmuztorg.next()
    await message.answer('Напишите ваш возраст')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmuztorg.age and 'age' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmuztorg.age)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['age'] = message.text
    await FSMmuztorg.next()
    await message.answer('Консультант подошел к Вам в течение 3 минут Вашего нахождения в его поле видимости?')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmuztorg.worker_3_minute and 'worker_3_minute' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmuztorg.worker_3_minute)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['worker_3_minute'] = message.text
    await FSMmuztorg.next()
    await message.answer('ФИО консультанта (Или описание внешности, если не удалось разглядеть бейдж)')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmuztorg.worker_name and 'worker_name' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmuztorg.worker_name)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['worker_name'] = message.text
    await FSMmuztorg.next()
    await message.answer('Внешний вид сотрудника соответствует стандартам?')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmuztorg.worker_appearance and 'worker_appearance' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmuztorg.worker_appearance)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['worker_appearance'] = message.text
    await FSMmuztorg.next()
    await message.answer('Внешний вид торгового зала соответствует стандартам?')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmuztorg.hall_appearance and 'hall_appearance' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmuztorg.hall_appearance)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['hall_appearance'] = message.text
    await FSMmuztorg.next()
    await message.answer('Консультант был приветлив и внимателен к Вам, как к клиенту?')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmuztorg.consultant_friendly and 'consultant_friendly' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmuztorg.consultant_friendly)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['consultant_friendly'] = message.text
    await FSMmuztorg.next()
    await message.answer('При отсутствии возможности провести консультацию самостоятельно консультант пригласил другого сотрудника и познакомил с Вами?')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmuztorg.other_consultant and 'other_consultant' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmuztorg.other_consultant)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['other_consultant'] = message.text
    await FSMmuztorg.next()
    await message.answer('Оцените общее впечатление от посещения магазина')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmuztorg.general_impression and 'general_impression' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmuztorg.general_impression)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['general_impression'] = message.text
    await FSMmuztorg.next()
    await message.answer('Оцените активность и заинтересованность консультирующего сотрудника')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmuztorg.consultant_activity and 'consultant_activity' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmuztorg.consultant_activity)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['consultant_activity'] = message.text
    await FSMmuztorg.next()
    await message.answer('Оцените компетентность консультирующего сотрудника')
    await asyncio.sleep(300)
    if await state.get_state() == FSMmuztorg.worker_competence and 'worker_competence' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMmuztorg.worker_competence)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['worker_competence'] = message.text
        await base.add_log(message.from_user.id, data_check['number'], 'Выполнил')
    await base.add_check("muztorg", state)
    await message.answer(f'Спасибо! Анкета {data_check["number"]} -- заполнена!', reply_markup=main_kb)
    await state.finish()

@dp.message_handler(content_types=[types.ContentType.TEXT, types.ContentType.PHOTO], state=[FSMmuztorg.photo2, FSMmuztorg.photo1])
async def photo_loop(message: types.Message, state: FSMContext):
    message_id = (await message.answer("Неверный формат сообщения.\n\nПожалуйста, пришлите фото")).message_id
    await asyncio.sleep(5)
    await bot.delete_message(message.from_user.id, message_id)

@dp.message_handler(content_types=[types.ContentType.TEXT, types.ContentType.PHOTO], state=FSMmuztorg.audio)
async def audio_loop(message: types.Message, state: FSMContext):
    message_id = (await message.answer("Неверный формат сообщения.\n\nПожалуйста, пришлите аудио")).message_id
    await asyncio.sleep(5)
    await bot.delete_message(message.from_user.id, message_id)

@dp.message_handler(state=FSMkastorama.date)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['date'] = message.text
    await FSMkastorama.next()
    await message.answer('Время начала проверки. Формат 17:20')
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.time and 'time' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMkastorama.time)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['time'] = message.text
    await FSMkastorama.next()
    await message.answer('Пришлите аудиозапись визита')
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.audio and 'audio' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMkastorama.audio, content_types=types.ContentType.AUDIO)
async def getting_audio(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['audio'] = message.audio.file_id
    await FSMmts.next()
    await message.answer('Прикрепите фото фасада')
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.photo and 'photo' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMkastorama.photo, content_types=types.ContentType.PHOTO)
async def getting_photo1(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['photo'] = f'https://api.telegram.org/file/bot5794915534:AAHb-BgGHR5eE3szwUsNYuyPKQ1x4CJaZBY/{(await bot.get_file(message.photo[-1].file_id))["file_path"]}'
    await FSMmts.next()
    await message.answer('Парковка чистая (нет мусора, нет тележек на парковочных местах, убрано от снега)', reply_markup=kastorama_kb)
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.parking_clear and 'parking_clear' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMkastorama.parking_clear)
async def getting_consultant_fitting(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['parking_clear'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer("На парковке есть свободные места", reply_markup=kastorama_kb)
    await FSMkastorama.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.parking_free and 'parking_free' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMkastorama.parking_free)
async def getting_consultant_fitting(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['parking_free'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer("На входе доступны тележки всех видов", reply_markup=kastorama_kb)
    await FSMkastorama.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.carts and 'carts' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMkastorama.carts)
async def getting_consultant_fitting(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['carts'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer("В туалетах чисто", reply_markup=kastorama_kb)
    await FSMkastorama.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.toilets_clear and 'toilets_clear' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMkastorama.toilets_clear)
async def getting_consultant_fitting(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['toilets_clear'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer("Замки во всех туалетных кабинках целые", reply_markup=kastorama_kb)
    await FSMkastorama.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.zamki and 'zamki' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMkastorama.zamki)
async def getting_consultant_fitting(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['zamki'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer("Вся сантехника в рабочем состоянии", reply_markup=kastorama_kb)
    await FSMkastorama.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.santehnika and 'santehnika' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMkastorama.santehnika)
async def getting_consultant_fitting(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['santehnika'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer("Легко можно найти информацию о том, где оформить доставку и забрать интернет-заказы", reply_markup=kastorama_kb)
    await FSMkastorama.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.info and 'info' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMkastorama.info)
async def getting_consultant_fitting(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['info'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer("По главной аллее магазина можно свободно перемещаться с тележкой", reply_markup=kastorama_kb)
    await FSMkastorama.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.cart_alley and 'cart_alley' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMkastorama.cart_alley)
async def getting_consultant_fitting(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['cart_alley'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer("Пришлите № кассового узла", reply_markup=kastorama_kb)
    await FSMkastorama.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.cash_number and 'cash_number' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMkastorama.cash_number)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['cash_number'] = message.text
    await FSMkastorama.next()
    await message.answer('ФИО кассира и описание внешности')
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.cashier_name and 'cashier_name' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMkastorama.cashier_name)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['cashier_name'] = message.text
    await FSMkastorama.next()
    await message.answer('Какой Вы по счету в очереди?')
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.queue_number and 'queue_number' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMkastorama.queue_number)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['queue_number'] = message.text
    await FSMkastorama.next()
    await message.answer('Засеките время с момента как Вы встали в очередь в кассу и до момента, когда кассир выдал Вам чек (мин.)')
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.queue_time and 'queue_time' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMkastorama.queue_time)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['queue_time'] = message.text
    await FSMkastorama.next()
    await message.answer('Внешний вид кассира соответствует установленным стандартам, бейдж присутствует, форма чистая, отглаженная. Если были нарушения, обязательно укажите')
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.cashier_appearance and 'cashier_appearance' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMkastorama.cashier_appearance)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['cashier_appearance'] = message.text
    await FSMkastorama.next()
    await message.answer('Работа с покупателем (Покупатель до Вас)')
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.worker_job_client and 'worker_job_client' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMkastorama.worker_job_client)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['worker_job_client'] = message.text
    await FSMkastorama.next()
    await message.answer('Кассир корректно просит покупателя предъявить к оплате весь выбранный товар, выложив его на кассовый прилавок (крупногабаритный товар осматривает непосредственно в тележке при помощи покупателя, корректно просит покупателя развернуть крупногабаритный товар штрих-кодом к кассиру)', reply_markup=kastorama_kb)
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.cashier_correctly and 'cashier_correctly' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMkastorama.cashier_correctly)
async def getting_consultant_fitting(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['cashier_correctly'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer("Легко можно найти информацию о том, где оформить доставку и забрать интернет-заказы", reply_markup=kastorama_kb)
    await FSMkastorama.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.cashier_barcode and 'cashier_barcode' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMkastorama.cashier_correctly)
async def getting_consultant_fitting(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['cashier_correctly'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer("Кассир сканировал штрих-код товара ИЛИ ввел штрих-код товара вручную, в случае, когда сканер не сработал", reply_markup=kastorama_kb)
    await FSMkastorama.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.cashier_barcode and 'cashier_barcode' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMkastorama.cashier_barcode)
async def getting_consultant_fitting(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['cashier_barcode'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer("При получении наличных денег от покупателя, кассир проверяет их платежеспособность на детекторах купюр или проверяет купюры «на ощупь»", reply_markup=kastorama_kb)
    await FSMkastorama.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.cashier_solvency and 'cashier_solvency' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMkastorama.cashier_solvency)
async def getting_consultant_fitting(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['cashier_solvency'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer("Кассир выдал сдачу покупателю вместе с чеком", reply_markup=kastorama_kb)
    await FSMkastorama.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.cashier_change and 'cashier_change' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMkastorama.cashier_change)
async def getting_consultant_fitting(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['cashier_change'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer("Работа с покупателем (При обслуживании Вас)")
    await FSMkastorama.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.cashier_job_user and 'cashier_job_user' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.message_handler(state=FSMkastorama.cashier_job_user)
async def getting_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['cashier_job_user'] = message.text
    await FSMkastorama.next()
    await message.answer('Кассир позитивно настроен, демонстрирует уверенность, доброжелательность, открытость', reply_markup=kastorama_kb)
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.cashier_positive and 'cashier_positive' not in (await state.get_data()).keys():
        await message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMkastorama.cashier_positive)
async def getting_consultant_fitting(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['cashier_change'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer("Кассир демонстрирует готовность помочь покупателю при необходимости")
    await FSMkastorama.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.cashier_help and 'cashier_help' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMkastorama.cashier_help)
async def getting_consultant_fitting(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['cashier_help'] = call.data.split("_")[1]
        await call.message.edit_text(call.message.text + "\n\n<b>✅Оценено</b>")
        await call.message.answer("Улыбается естественно и доброжелательно ИЛИ доброжелательное выражение лица без явной наигранной улыбки")
    await FSMkastorama.next()
    await asyncio.sleep(300)
    if await state.get_state() == FSMkastorama.cashier_benevolence and 'cashier_benevolence' not in (await state.get_data()).keys():
        await call.message.answer("Вы тут? Возможно вы забыли продолжить заполнять анкету")

@dp.callback_query_handler(Text(startswith="grade_"), state=FSMkastorama.cashier_help)
async def getting_consultant_fitting(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data_check:
        data_check['cashier_benevolence'] = call.data.split("_")[1]
        await call.message.edit_text(f"Спасибо. Анкета - {data_check['number']} заполнена")
        await base.add_check("kastorama", data_check)
        await base.add_log(call.from_user.id, data_check['number'], "Взял")
    await state.finish()

