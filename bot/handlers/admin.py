import logging
from datetime import datetime

from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import ADMIN_IDS, SUPPORT_BOT
from bot.instance import bot, router
from shared.config import PLANS
from shared.database import (
    db_add_balance,
    db_add_news,
    db_ensure_user,
    db_list_subs,
    db_remove_sub,
)
from shared.provision import provision_sub

log = logging.getLogger(__name__)


class AdminStates(StatesGroup):
    givesub_id = State()
    givesub_plan = State()
    givesub_days = State()
    removesub_id = State()
    addbal_id = State()
    addbal_amt = State()
    news_text = State()
    notify_id = State()
    notify_text = State()


def is_admin(tg_id: int) -> bool:
    return tg_id in ADMIN_IDS


def kb_cancel():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel"))
    return b.as_markup()


def kb_plans():
    b = InlineKeyboardBuilder()
    for pid, p in PLANS.items():
        b.row(InlineKeyboardButton(text=p["name"].capitalize(), callback_data=f"adm_plan_{pid}"))
    b.row(InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel"))
    return b.as_markup()


def get_listsub_text_and_kb(subs: list, page_idx: int):
    plan_keys = list(PLANS.keys())
    total_pages = len(plan_keys)

    if total_pages == 0:
        return "Не настроены тарифы в конфигурации.", None

    page_idx = page_idx % total_pages
    plan_key = plan_keys[page_idx]
    plan_name = PLANS[plan_key].get("name", plan_key).capitalize()

    plan_subs = [s for s in subs if s["plan"] == plan_key]

    text = f"📋 <b>Активные подписки | {plan_name}</b>\n"
    text += f"📄 <i>Страница {page_idx + 1} из {total_pages}</i>\n\n"

    if not plan_subs:
        text += "Нет активных подписок.\n"
    else:
        for i, s in enumerate(plan_subs, 1):
            exp = datetime.fromisoformat(str(s["expires_at"]))
            days_left = max(0, (exp - datetime.now()).days)

            if s.get("username"):
                uname = f"@{s['username']}"
            elif s.get("first_name"):
                uname = s["first_name"]
            else:
                uname = "—"

            text += f"<b>{i}.</b> <code>{s['tg_id']}</code> · {uname}\n"
            text += f" ⏳ до {exp.strftime('%d.%m.%y')} ({days_left} дн.)\n\n"

    if len(text) > 4000:
        text = text[:3900] + "\n\n... (список обрезан)"

    b = InlineKeyboardBuilder()
    prev_p = (page_idx - 1) % total_pages
    next_p = (page_idx + 1) % total_pages
    b.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"listsub_page_{prev_p}"),
        InlineKeyboardButton(text="Вперед ➡️", callback_data=f"listsub_page_{next_p}"),
    )
    b.row(InlineKeyboardButton(text="❌ Закрыть", callback_data="admin_cancel"))

    return text, b.as_markup()


# ====================== КОМАНДЫ ======================

@router.callback_query(F.data == "admin_cancel")
async def cb_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Отменено.")


@router.callback_query(F.data.startswith("listsub_page_"))
async def cb_listsub_page(call: CallbackQuery):
    page_idx = int(call.data.split("_")[-1])
    subs = await db_list_subs()
    text, kb = get_listsub_text_and_kb(subs, page_idx)
    try:
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        pass
    await call.answer()


@router.message(Command("givesub"))
async def cmd_givesub(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await state.clear()
    args = msg.text.split()[1:]
    if len(args) >= 3:
        try:
            return await _do_givesub(msg, int(args[0]), args[1], int(args[2]))
        except (ValueError, IndexError):
            pass
    await state.set_state(AdminStates.givesub_id)
    await msg.answer(
        "🎁 <b>Выдача подписки</b>\n\nTelegram ID пользователя:",
        parse_mode="HTML",
        reply_markup=kb_cancel(),
    )


@router.message(Command("removesub"))
async def cmd_removesub(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await state.clear()
    args = msg.text.split()[1:]
    if args:
        try:
            return await _do_removesub(msg, int(args[0]))
        except ValueError:
            pass
    await state.set_state(AdminStates.removesub_id)
    await msg.answer(
        "❌ <b>Удаление подписки</b>\n\nTelegram ID:",
        parse_mode="HTML",
        reply_markup=kb_cancel(),
    )


@router.message(Command("listsub"))
async def cmd_listsub(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await state.clear()
    subs = await db_list_subs()
    text, kb = get_listsub_text_and_kb(subs, page_idx=0)
    if kb:
        await msg.answer(text, parse_mode="HTML", reply_markup=kb)
    else:
        await msg.answer(text, parse_mode="HTML")


@router.message(Command("addbalance"))
async def cmd_addbalance(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await state.clear()
    args = msg.text.split()[1:]
    if len(args) >= 2:
        try:
            return await _do_addbalance(msg, int(args[0]), int(args[1]))
        except ValueError:
            pass
    await state.set_state(AdminStates.addbal_id)
    await msg.answer(
        "💰 <b>Пополнение баланса</b>\n\nTelegram ID:",
        parse_mode="HTML",
        reply_markup=kb_cancel(),
    )


@router.message(Command("news"))
async def cmd_news(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await state.clear()
    txt = msg.text[len("/news"):].strip()
    if txt:
        return await _do_news(msg, txt)
    await state.set_state(AdminStates.news_text)
    await msg.answer("📣 Введи текст новости:", reply_markup=kb_cancel())


@router.message(Command("notify"))
async def cmd_notify(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await state.clear()
    parts = msg.text.split(maxsplit=2)[1:]
    if len(parts) >= 2:
        try:
            return await _do_notify(msg, int(parts[0]), parts[1])
        except (ValueError, IndexError):
            pass
    await state.set_state(AdminStates.notify_id)
    await msg.answer(
        "📧 <b>Уведомление пользователю</b>\n\nTelegram ID:",
        parse_mode="HTML",
        reply_markup=kb_cancel(),
    )


@router.message(Command("help"))
async def cmd_help(msg: Message, state: FSMContext):
    await state.clear()
    if is_admin(msg.from_user.id):
        plans_list = ", ".join([p.capitalize() for p in PLANS.keys()])
        text = (
            "🛠 <b>Панель управления администратора</b>\n\n"
            "<b>Управление подписками:</b>\n"
            "🔸 <code>/givesub {id} {plan} {days}</code> — Выдать подписку\n"
            "🔸 <code>/removesub {id}</code> — Аннулировать подписку\n"
            "🔸 <code>/listsub</code> — Список пользователей (по тарифам)\n\n"
            "<b>Финансы и баланс:</b>\n"
            "🔸 <code>/addbalance {id} {sum}</code> — Начислить средства\n\n"
            "<b>Коммуникация:</b>\n"
            "🔸 <code>/news {текст}</code> — Опубликовать новость\n"
            "🔸 <code>/notify {id} {текст}</code> — Отправить личное сообщение\n\n"
            f"<b>Доступные тарифы:</b>\n🔹 {plans_list}\n\n"
            "<i>Все команды поддерживают пошаговый ввод без аргументов.</i>"
        )
    else:
        text = (
            "🤖 <b>Навигация по боту</b>\n\n"
            "🔹 <b>/start</b> — Главное меню\n"
            "🔹 <b>/lk</b> — Личный кабинет и ключ доступа\n"
            "🔹 <b>/balance</b> — Состояние счета и пополнение\n"
            "🔹 <b>/instructions</b> — Руководство по настройке VPN\n\n"
            f"<i>Остались вопросы? Обращайтесь в поддержку: {SUPPORT_BOT}</i>"
        )
    await msg.answer(text, parse_mode="HTML")


# ====================== ХЕНДЛЕРЫ СОСТОЯНИЙ ======================

@router.message(AdminStates.givesub_id, ~F.text.startswith("/"))
async def gs_id(msg: Message, state: FSMContext):
    if not msg.text.strip().isdigit():
        return await msg.answer("❌ ID — только цифры.")
    await state.update_data(tid=int(msg.text.strip()))
    await state.set_state(AdminStates.givesub_plan)
    await msg.answer("Выбери тариф:", reply_markup=kb_plans())


@router.callback_query(AdminStates.givesub_plan, F.data.startswith("adm_plan_"))
async def gs_plan(call: CallbackQuery, state: FSMContext):
    plan = call.data[9:]
    if plan not in PLANS:
        return await call.answer("Неизвестный тариф.")
    await state.update_data(plan=plan)
    await state.set_state(AdminStates.givesub_days)
    await call.message.edit_text("📅 Количество дней (например, 30):", reply_markup=kb_cancel())


@router.message(AdminStates.givesub_days, ~F.text.startswith("/"))
async def gs_days(msg: Message, state: FSMContext):
    txt = msg.text.strip()
    if not txt.isdigit() or int(txt) <= 0:
        return await msg.answer("❌ Введи положительное число.")
    data = await state.get_data()
    await state.clear()
    await _do_givesub(msg, data["tid"], data["plan"], int(txt))


@router.message(AdminStates.removesub_id, ~F.text.startswith("/"))
async def rs_id(msg: Message, state: FSMContext):
    if not msg.text.strip().isdigit():
        return await msg.answer("❌ ID — только цифры.")
    await state.clear()
    await _do_removesub(msg, int(msg.text.strip()))


@router.message(AdminStates.addbal_id, ~F.text.startswith("/"))
async def ab_id(msg: Message, state: FSMContext):
    if not msg.text.strip().isdigit():
        return await msg.answer("❌ ID — только цифры.")
    await state.update_data(tid=int(msg.text.strip()))
    await state.set_state(AdminStates.addbal_amt)
    await msg.answer("Сумма (₽):", reply_markup=kb_cancel())


@router.message(AdminStates.addbal_amt, ~F.text.startswith("/"))
async def ab_amt(msg: Message, state: FSMContext):
    txt = msg.text.strip()
    if not txt.isdigit() or int(txt) <= 0:
        return await msg.answer("❌ Введи положительное число.")
    data = await state.get_data()
    await state.clear()
    await _do_addbalance(msg, data["tid"], int(txt))


@router.message(AdminStates.news_text, ~F.text.startswith("/"))
async def news_text_h(msg: Message, state: FSMContext):
    txt = msg.text.strip()
    if not txt:
        return await msg.answer("❌ Пустой текст.")
    await state.clear()
    await _do_news(msg, txt)


@router.message(AdminStates.notify_id, ~F.text.startswith("/"))
async def notify_id_h(msg: Message, state: FSMContext):
    if not msg.text.strip().isdigit():
        return await msg.answer("❌ ID — только цифры.")
    await state.update_data(tid=int(msg.text.strip()))
    await state.set_state(AdminStates.notify_text)
    await msg.answer("Текст сообщения:", reply_markup=kb_cancel())


@router.message(AdminStates.notify_text, ~F.text.startswith("/"))
async def notify_text_h(msg: Message, state: FSMContext):
    txt = msg.text.strip()
    if not txt:
        return await msg.answer("❌ Пустой текст.")
    data = await state.get_data()
    await state.clear()
    await _do_notify(msg, data["tid"], txt)


# ====================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ======================

async def _do_givesub(msg: Message, tid: int, plan: str, days: int):
    if plan not in PLANS:
        return await msg.answer(f"❌ Тариф <code>{plan}</code> не найден.", parse_mode="HTML")
    try:
        await db_ensure_user(tid, None, str(tid))
        await provision_sub(tid, plan, days)
        name = PLANS[plan]["name"].capitalize()
        await msg.answer(
            f"✅ <b>Подписка выдана</b>\n\nПользователь: <code>{tid}</code>\nТариф: {name} · {days} дн.",
            parse_mode="HTML",
        )
        try:
            await bot.send_message(
                tid,
                f"🎁 <b>Подписка активирована!</b>\nТариф: <b>{name}</b> · {days} дн.",
                parse_mode="HTML",
            )
        except Exception:
            pass
    except Exception as e:
        log.error("givesub", exc_info=True)
        await msg.answer(f"❌ Ошибка: {e}")


async def _do_removesub(msg: Message, tid: int):
    await db_remove_sub(tid)
    await msg.answer(f"✅ Подписка удалена\nПользователь: <code>{tid}</code>", parse_mode="HTML")


async def _do_addbalance(msg: Message, tid: int, amt: int):
    try:
        await db_ensure_user(tid, None, str(tid))
        new_bal = await db_add_balance(tid, amt)
        await msg.answer(
            f"✅ <b>Баланс пополнен</b>\n\nПользователь: <code>{tid}</code>\nНачислено: {amt} ₽ · Итого: {new_bal} ₽",
            parse_mode="HTML",
        )
        try:
            await bot.send_message(
                tid,
                f"💳 Баланс пополнен на <b>{amt} ₽</b>\nИтого: <b>{new_bal} ₽</b>",
                parse_mode="HTML",
            )
        except Exception:
            pass
    except Exception as e:
        log.error("addbalance", exc_info=True)
        await msg.answer(f"❌ Ошибка: {e}")


async def _do_news(msg: Message, txt: str):
    try:
        await db_add_news(txt)
        await msg.answer("✅ Новость сохранена и будет разослана.")
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")


async def _do_notify(msg: Message, tid: int, text: str):
    try:
        await bot.send_message(tid, text)
        await msg.answer(f"✅ Сообщение успешно отправлено пользователю <code>{tid}</code>.", parse_mode="HTML")
    except Exception as e:
        await msg.answer(f"❌ Не удалось отправить сообщение: {e}")
