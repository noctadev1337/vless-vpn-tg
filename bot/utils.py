import os
import logging

from aiogram.types import FSInputFile, Message

from bot.config import BANNER_PATH, BANNER_URL, CHANNEL_ID
from bot.instance import bot, _last
from shared.config import DOMAIN, DOMAIN_BACKUP

log = logging.getLogger(__name__)


def sub_url(key: str) -> str:
    return f"https://{DOMAIN}/{key}"


def sub_url_backup(key: str) -> str:
    return f"https://{DOMAIN_BACKUP}/{key}"


def fmt_traffic(used_b: int, limit_b: int) -> str:
    used_gb = used_b / 1024 ** 3
    if limit_b > 0:
        lim_gb = limit_b / 1024 ** 3
        return f"{used_gb:.1f} / {lim_gb:.0f} ГБ"
    return f"{used_gb:.1f} ГБ / ∞"


async def delete_last(chat_id: int):
    mids = _last.pop(chat_id, [])
    if isinstance(mids, int):
        mids = [mids]
    for mid in mids:
        try:
            await bot.delete_message(chat_id, mid)
        except Exception:
            pass


async def send(chat_id: int, text: str, kb=None, delete_prev: bool = True):
    if delete_prev:
        await delete_last(chat_id)
    photo = FSInputFile(BANNER_PATH) if os.path.exists(BANNER_PATH) else BANNER_URL
    msg = await bot.send_photo(
        chat_id, photo=photo, caption=text,
        reply_markup=kb, parse_mode="HTML",
    )
    _last.setdefault(chat_id, []).append(msg.message_id)
    return msg


async def try_delete(msg: Message):
    try:
        await msg.delete()
    except Exception:
        pass


async def is_subscribed(tg_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, tg_id)
        return member.status not in ("left", "kicked", "banned")
    except Exception as e:
        log.warning(f"Channel check failed for {tg_id}: {e}")
        return True
