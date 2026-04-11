import logging

from aiogram import F
from aiogram.types import CallbackQuery

from bot.instance import router
from bot.keyboards import kb_shop, kb_go_lk
from bot.texts import t_shop, t_activated
from bot.utils import send
from shared.config import PLANS
from shared.database import db_get_sub, db_get_balance, db_deduct_balance
from shared.provision import provision_sub

log = logging.getLogger(__name__)


@router.callback_query(F.data == "shop")
async def cb_shop(call: CallbackQuery):
    await call.answer()
    tg_id = call.from_user.id
    sub = await db_get_sub(tg_id)
    balance = await db_get_balance(tg_id)
    await send(tg_id, t_shop(bool(sub), sub, balance), kb_shop())


@router.callback_query(F.data.startswith("buy_"))
async def cb_buy(call: CallbackQuery):
    await call.answer()
    plan_id = call.data[4:]
    plan = PLANS.get(plan_id)
    if not plan or plan["hidden"]:
        return

    tg_id = call.from_user.id
    balance = await db_get_balance(tg_id)
    tr = "∞ ГБ" if plan["traffic_gb"] == 0 else f"{plan['traffic_gb']} ГБ"

    # проверяем — есть ли активная подписка (продление или покупка)
    sub = await db_get_sub(tg_id)
    is_renew = sub is not None

    shortage = plan["price"] - balance
    balance_ok = balance >= plan["price"]
    if balance_ok:
        balance_line = f"💰 Баланс: <b>{balance} ₽</b> — достаточно для оплаты"
    else:
        balance_line = (
            f"💳 Нужно <b>{plan['price']} ₽</b>, на балансе <b>{balance} ₽</b>\n"
            f"Не хватает <b>{shortage} ₽</b> — пополни и вернись"
        )

    action_label = "продления" if is_renew else "покупки"

    text = (
        f"🛒 <b>Подтверждение {action_label}</b>\n\n"
        f"📦 Тариф: <b>{plan['name']}</b>\n\n"
        f"<blockquote>"
        f"📊 Трафик — <b>{tr}</b>\n"
        f"📱 Устройств — <b>{plan['devices']}</b>\n"
        f"📅 Срок — <b>30 дней</b>\n"
        f"💰 Стоимость — <b>{plan['price']} ₽</b>"
        f"</blockquote>\n\n"
        f"{balance_line}"
    )

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    b = InlineKeyboardBuilder()
    if balance >= plan["price"]:
        b.row(InlineKeyboardButton(
            text=f"{'🔄 Продлить' if is_renew else '✅ Оплатить'} — {plan['price']} ₽",
            callback_data=f"confirm_{plan_id}",
        ))
    b.row(InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="topup"))
    b.row(InlineKeyboardButton(text="◀️ Назад", callback_data="shop"))
    await send(tg_id, text, b.as_markup())


@router.callback_query(F.data.startswith("confirm_"))
async def cb_confirm(call: CallbackQuery):
    await call.answer("Обрабатываем...", show_alert=False)
    plan_id = call.data[8:]
    plan = PLANS.get(plan_id)
    if not plan or plan["hidden"]:
        return

    tg_id = call.from_user.id

    # атомарное списание
    if not await db_deduct_balance(tg_id, plan["price"]):
        await call.answer("❌ Недостаточно средств на балансе.", show_alert=True)
        return

    try:
        key, expires_at = await provision_sub(tg_id, plan_id, plan["days"])
    except Exception as e:
        # откатываем списание при ошибке provision
        from shared.database import db_add_balance
        await db_add_balance(tg_id, plan["price"])
        log.error(f"provision_sub failed for {tg_id}/{plan_id}: {e}")
        await call.answer("❌ Ошибка активации. Средства возвращены.", show_alert=True)
        return

    sub = await db_get_sub(tg_id)
    balance = await db_get_balance(tg_id)

    from datetime import datetime
    from shared.config import PLANS as _PLANS
    days_left = max(0, (expires_at - datetime.now()).days)

    text = t_activated(plan_id, key, expires_at, plan["days"])
    text += f"\n\n💰 Остаток на балансе: <b>{balance} ₽</b>"

    await send(tg_id, text, kb_go_lk(key))
