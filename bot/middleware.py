from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery
from bot.instance import _last


class TrackSourceMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: CallbackQuery, data: dict):
        chat_id = event.from_user.id
        msg_id = event.message.message_id
        lst = _last.setdefault(chat_id, [])
        if msg_id not in lst:
            lst.append(msg_id)
        return await handler(event, data)
