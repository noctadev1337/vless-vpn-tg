from aiogram import F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.instance import router
from bot.keyboards import kb_lk
from bot.texts import t_lk
from bot.utils import send, try_delete, fmt_traffic
from shared.database import db_get_sub, db_get_balance
from shared.xui import xui, get_xui2


async def _get_traffic(sub) -> dict:
    """Суммирует трафик с основного + дополнительного серверов."""
    if not sub:
        return {}
    up, down = 0, 0
    try:
        t1 = await xui.get_traffic(sub["xui_email"])
        up += t1.get("up") or 0
        down += t1.get("down") or 0
    except Exception:
        pass
    if sub["xui_uuid2"]:
        try:
            t2 = await get_xui2().get_traffic(sub["xui_email"])
            up += t2.get("up") or 0
            down += t2.get("down") or 0
        except Exception:
            pass
    return {"up": up, "down": down}


@router.callback_query(F.data == "lk")
async def cb_lk(call: CallbackQuery):
    await call.answer()
    tg_id = call.from_user.id
    sub = await db_get_sub(tg_id)
    tr = await _get_traffic(sub)
    key = sub["key"] if sub else None
    balance = await db_get_balance(tg_id)
    await send(tg_id, t_lk(sub, tr, balance), kb_lk(bool(sub), key))


@router.message(Command("lk"))
async def cmd_lk(msg: Message):
    await try_delete(msg)
    tg_id = msg.from_user.id
    sub = await db_get_sub(tg_id)
    tr = await _get_traffic(sub)
    key = sub["key"] if sub else None
    balance = await db_get_balance(tg_id)
    await send(tg_id, t_lk(sub, tr, balance), kb_lk(bool(sub), key))


@router.message(Command("balance"))
async def cmd_balance(msg: Message):
    await try_delete(msg)
    tg_id = msg.from_user.id
    balance = await db_get_balance(tg_id)
    from bot.handlers.topup import kb_balance
    await send(
        tg_id,
        f"💰 <b>Баланс</b>\n\nТекущий баланс: <b>{balance} ₽</b>",
        kb_balance(),
    )