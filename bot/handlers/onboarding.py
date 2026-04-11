from aiogram import F
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from bot.instance import router, _last
from bot.keyboards import kb_agree, kb_channel, kb_main, kb_trial_after
from bot.texts import t_agree, t_channel, t_welcome, t_trial_activated
from bot.utils import is_subscribed, send
from shared.database import db_agree, db_ensure_user, db_get_user, db_get_sub, db_has_used_trial
from shared.provision import provision_sub


async def _show_main(chat_id: int, name: str):
    sub = await db_get_sub(chat_id)
    has_trial = await db_has_used_trial(chat_id)
    show_trial = not sub and not has_trial
    await send(chat_id, t_welcome(name), kb_main(show_trial=show_trial))


@router.message(CommandStart())
async def cmd_start(msg: Message):
    tg_id = msg.from_user.id
    name = msg.from_user.first_name or "друг"
    await db_ensure_user(tg_id, msg.from_user.username, name)
    user = await db_get_user(tg_id)
    if not user["agreed"]:
        await send(tg_id, t_agree(name), kb_agree())
        return
    if not await is_subscribed(tg_id):
        await send(tg_id, t_channel(), kb_channel())
        return
    await _show_main(tg_id, name)


@router.callback_query(F.data == "agree")
async def cb_agree(call: CallbackQuery):
    await call.answer()
    tg_id = call.from_user.id
    name = call.from_user.first_name or "друг"
    await db_agree(tg_id)
    if not await is_subscribed(tg_id):
        await send(tg_id, t_channel(), kb_channel())
        return
    await _show_main(tg_id, name)


@router.callback_query(F.data == "check_sub")
async def cb_check_channel(call: CallbackQuery):
    await call.answer()
    tg_id = call.from_user.id
    name = call.from_user.first_name or "друг"
    if not await is_subscribed(tg_id):
        await call.answer("Ты ещё не подписан 😔", show_alert=True)
        return
    await _show_main(tg_id, name)


@router.callback_query(F.data == "menu")
async def cb_menu(call: CallbackQuery):
    await call.answer()
    name = call.from_user.first_name or "друг"
    try:
        await call.message.delete()
    except Exception:
        pass
    _last.pop(call.from_user.id, None)
    await _show_main(call.from_user.id, name)


@router.callback_query(F.data == "trial")
async def cb_trial(call: CallbackQuery):
    await call.answer()
    tg_id = call.from_user.id

    if await db_has_used_trial(tg_id) or await db_get_sub(tg_id):
        await call.answer("Пробный период уже был использован 😔", show_alert=True)
        return

    key, _ = await provision_sub(tg_id, "trial", 1)
    await send(tg_id, t_trial_activated(key), kb_trial_after(key))
