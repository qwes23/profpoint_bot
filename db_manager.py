# -*- coding: utf-8 -*-
import os

import aiosqlite


class DatabaseManager:
    async def create_tables(self):
        with open('main.db', "a") as file:
            pass
        async with aiosqlite.connect('main.db') as db:
            await db.execute(
                """CREATE TABLE IF NOT EXISTS users(id INTEGER NOT NULL, name TEXT, surname TEXT, email TEXT, phone TEXT, telegram_name TEXT);""")
            await db.execute(
                """CREATE TABLE IF NOT EXISTS log(id INTEGER NOT NULL, name TEXT, surname TEXT, proverka TEXT, action TEXT);""")
            await db.execute("""CREATE TABLE IF NOT EXISTS checks(id INT, user_id INT, company TEXT);""")
            await db.commit()

    async def user_exists(self, userid):
        async with aiosqlite.connect('main.db') as db:
            return bool(
                await (await db.execute("""SELECT * FROM users WHERE id== ?""", (int(userid),))).fetchall())

    async def add_user(self, data):
        async with aiosqlite.connect('main.db') as db:
            await db.execute("""INSERT INTO users VALUES(?, ?, ?, ?, ?, ?)""", tuple(data))
            await db.commit()

    async def get_help_info(self, userid):
        async with aiosqlite.connect('main.db') as db:
            ex = await db.execute("""SELECT * FROM users WHERE id == ?""", (userid,))
            return await ex.fetchone()

    async def get_user_info(self, userid):
        async with aiosqlite.connect('main.db', timeout=20) as db:
            ex = await db.execute("""SELECT name, surname FROM users WHERE id == ?""", (userid,))
        return await ex.fetchone()

    async def add_log(self, userid, check_id, action):
        async with aiosqlite.connect('main.db', timeout=20) as db:
            ex = await db.execute("""SELECT name, surname FROM users WHERE id == ?""", (userid,))
            user_info = await ex.fetchone()
            await db.execute("""INSERT INTO log VALUES(?, ?, ?, ?, ?);""", (userid, user_info[0], user_info[1], check_id, action))
            await db.commit()

    async def get_available_checks(self, latitude1, longitude1, latitude2, longitude2):
        companies = os.listdir("db")
        checks = []
        for company in companies:
            async with aiosqlite.connect('db/' + company, timeout=20) as db:
                ex = await db.execute(
                    """SELECT id, adress FROM adress WHERE latitude BETWEEN (?) AND (?) AND longitude BETWEEN (?) AND (?) AND assigned = 0 AND done = 0""",
                    (latitude1, latitude2, longitude1, longitude2))
                for check in await ex.fetchall():
                    edited_check = list(check)
                    edited_check.append(company.split(".")[0])
                    checks.append(edited_check)
        return checks

    async def assignate_check(self, userid, checkid):
        companies = os.listdir("db")
        for company in companies:
            async with aiosqlite.connect('db/' + company, timeout=20) as db:
                ex = await db.execute("""SELECT * FROM adress WHERE id == ?""", (checkid,))
                is_db_have_check = await ex.fetchone()
                if is_db_have_check and is_db_have_check[-1] != 1:
                    await db.execute("""UPDATE adress SET assigned == ? WHERE id == ?""", (userid, checkid))
                    await db.commit()
                    async with aiosqlite.connect('main.db', timeout=20) as main_db:
                        await main_db.execute("""INSERT INTO checks VALUES(?, ?, ?);""", (checkid, userid, company.split(".")[0]))
                        await main_db.commit()
                    return 1
        return 0

    async def get_user_checks(self, userid):
        companies = os.listdir("db")
        checks = []
        for company in companies:
            async with aiosqlite.connect('db/' + company, timeout=20) as db:
                ex = await db.execute("""SELECT id, adress FROM adress WHERE assigned == ?""", (userid,))
                db_checks = await ex.fetchall()
                checks.extend(db_checks)
        return checks

    async def cancel_check(self, checkid):
        companies = os.listdir("db")
        for company in companies:
            async with aiosqlite.connect('db/' + company, timeout=20) as db:
                ex = await db.execute("""SELECT * FROM adress WHERE id == ?""", (checkid,))
                is_db_have_check = await ex.fetchone()
                if is_db_have_check:
                    await db.execute("""UPDATE adress SET assigned == ? WHERE id == ?""", (0, checkid))
                    await db.commit()
                    return 1

    async def is_user_have_check(self, userid, checkid):
        companies = os.listdir("db")
        for company in companies:
            async with aiosqlite.connect('db/' + company, timeout=20) as db:
                ex = await db.execute("""SELECT assigned FROM adress WHERE id == ?""", (checkid,))
                db_check = await ex.fetchone()
                if db_check:
                    if db_check[0] == userid:
                        return company.split(".")[0]

    async def add_check(self, company, state):
        async with state.proxy() as data:
            if company == "sokolov":
                async with aiosqlite.connect('db/sokolov.db', timeout=20) as db:
                    await db.execute("""INSERT INTO proverka 
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""", (data['user_id'], data['number'], data['date_time'], data['date'],
                                                                        data['time_start'], data['audio'], data['worker_name'],
                                                                        data['worker_count'], data['client_count'], data['worker_job'],
                                                                        data['worker_substrate'], data['worker_friendliness'], data['worker_service']))
                    await db.execute("""UPDATE adress SET done == ? WHERE id == ?""", (1, data['number']))
                    await db.commit()
            elif company == "mts":
                async with aiosqlite.connect('db/mts.db', timeout=20) as db:
                    await db.execute("INSERT INTO proverka VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", tuple(list(data.values())[1:]))
                    await db.execute("""UPDATE adress SET done == ? WHERE id == ?""", (1, data['number']))
                    await db.commit()
            elif company == "gate31":
                async with aiosqlite.connect('db/gate31.db', timeout=20) as db:
                    await db.execute(
                        "INSERT INTO proverka VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        tuple(list(data.values())[1:]))
                    await db.execute("""UPDATE adress SET done == ? WHERE id == ?""", (1, data['number']))
                    await db.commit()
            elif company == "irbis":
                async with aiosqlite.connect('db/irbis.db', timeout=20) as db:
                    await db.execute(
                        "INSERT INTO proverka VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        tuple(list(data.values())[1:]))
                    await db.execute("""UPDATE adress SET done == ? WHERE id == ?""", (1, data['number']))
                    await db.commit()
            elif company == "muztorg":
                async with aiosqlite.connect('db/muztorg.db', timeout=20) as db:
                    await db.execute(
                        "INSERT INTO proverka VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        tuple(list(data.values())[1:]))
                    await db.execute("""UPDATE adress SET done == ? WHERE id == ?""", (1, data['number']))
                    await db.commit()
            elif company == "kastorama":
                async with aiosqlite.connect('db/kastorama.db', timeout=20) as db:
                    await db.execute(
                        "INSERT INTO proverka VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        tuple(list(data.values())[1:]))
                    await db.execute("""UPDATE adress SET done == ? WHERE id == ?""", (1, data['number']))
                    await db.commit()
            elif company == "subway":
                async with aiosqlite.connect('db/subway.db', timeout=20) as db:
                    await db.execute(
                        "INSERT INTO proverka VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        tuple(list(data.values())[1:]))
                    await db.execute("""UPDATE adress SET done == ? WHERE id == ?""", (1, data['number']))
                    await db.commit()