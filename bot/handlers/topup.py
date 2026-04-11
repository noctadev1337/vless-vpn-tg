import base64
import logging
import uuid
import aiohttp

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.instance import router
from bot.utils import send, try_delete
from shared.config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY, BOT_LINK
from shared.database import db_create_topup, db_get_balance

log = logging.getLogger(__name__)

MIN_TOPUP = 100


class TopupStates(StatesGroup):
    waiting_amount = State()


def kb_balance():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="topup_start"))
    b.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu"))
    return b.as_markup()


def kb_cancel_topup(back: str = "topup"):
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="❌ Отмена", callback_data=back))
    return b.as_markup()


def kb_topup_pay(payment_url: str, back: str = "topup"):
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🏦 Перейти к оплате", url=payment_url))
    b.row(InlineKeyboardButton(text="◀️ Назад", callback_data=back))
    return b.as_markup()


async def _create_topup_payment(tg_id: int, amount: int) -> dict | None:
    """Создание платежа в ЮKassa через API v3."""
    user_auth = f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}".encode()
    auth = base64.b64encode(user_auth).decode()

    payload = {
        "amount": {"value": f"{amount}.00", "currency": "RUB"},
        "confirmation": {
            "type": "redirect",
            "return_url": BOT_LINK  # Ссылка на бота из конфига
        },
        "capture": True,
        "description": f"Пополнение баланса (ID: {tg_id}) на {amount} руб",
        "metadata": {
            "tg_id": str(tg_id),
            "type": "topup",
            "amount": str(amount)
        },
        "payment_method_data": {"type": "sbp"},  # Принудительно СБП для удобства
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    "https://api.yookassa.ru/v3/payments",
                    json=payload,
                    headers={
                        "Authorization": f"Basic {auth}",
                        "Idempotence-Key": str(uuid.uuid4()),
                        "Content-Type": "application/json",
                    },
                    timeout=15
            ) as response:
                data = await response.json()
                if response.status == 200 and "id" in data:
                    return data
                log.error(f"YooKassa API Error ({response.status}): {data}")
    except Exception as e:
        log.error(f"YooKassa request failed: {e}")
    return None


@router.callback_query(F.data == "topup")
async def cb_topup(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.clear()

    tg_id = call.from_user.id
    balance = await db_get_balance(tg_id)

    await send(
        tg_id,
        f"💰 <b>Ваш баланс</b>\n\nТекущий остаток: <b>{balance} ₽</b>\n\n"
        f"Вы можете пополнить баланс для приобретения доступа к сервису.",
        kb_balance(),
    )


@router.callback_query(F.data == "topup_start")
async def cb_topup_start(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(TopupStates.waiting_amount)

    await send(
        call.from_user.id,
        f"✏️ <b>Введите сумму пополнения</b>\n\n"
        f"Минимальная сумма: <b>{MIN_TOPUP} ₽</b>\n"
        f"Введите только число (например: 250).",
        kb_cancel_topup(back="topup"),
    )


@router.message(TopupStates.waiting_amount, ~F.text.startswith('/'))
async def topup_amount_input(msg: Message, state: FSMContext):
    await try_delete(msg)

    raw_text = msg.text.strip().replace(" ", "").replace(",", ".")
    try:
        amount = int(float(raw_text))
    except ValueError:
        return await send(
            msg.from_user.id,
            f"❌ Некорректный ввод.\nВведите сумму числом (минимум <b>{MIN_TOPUP} ₽</b>).",
            kb_cancel_topup(back="topup"),
        )

    if amount < MIN_TOPUP:
        return await send(
            msg.from_user.id,
            f"❌ Сумма слишком мала.\nМинимальное пополнение — <b>{MIN_TOPUP} ₽</b>.",
            kb_cancel_topup(back="topup"),
        )

    await state.clear()
    await _process_topup(msg.from_user.id, amount)


async def _process_topup(tg_id: int, amount: int):
    # Индикация загрузки (опционально можно добавить сообщение "Создаем счет...")
    payment = await _create_topup_payment(tg_id, amount)

    if not payment:
        return await send(
            tg_id,
            "❌ Не удалось создать платеж. Пожалуйста, обратитесь в поддержку или попробуйте позже."
        )

    payment_id = payment["id"]
    payment_url = payment["confirmation"]["confirmation_url"]

    # Сохраняем в БД ожидающий платеж
    await db_create_topup(payment_id, tg_id, amount)

    await send(
        tg_id,
        f"💳 <b>Счет на {amount} ₽ сформирован</b>\n\n"
        f"Для оплаты нажмите кнопку ниже. После завершения транзакции "
        f"баланс будет зачислен автоматически в течение пары минут.",
        kb_topup_pay(payment_url, back="topup"),
    )
