from aiogram import Dispatcher

from .throttling import ThrottlingMiddleware, AlbumMiddleware


def setup(dp: Dispatcher):
    dp.middleware.setup(AlbumMiddleware())
    dp.middleware.setup(ThrottlingMiddleware())