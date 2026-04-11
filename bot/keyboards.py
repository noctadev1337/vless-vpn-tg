from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import SUPPORT_LINK, CHANNEL_ID
from bot.utils import sub_url, sub_url_backup

BTNS = {
    "agree": "✅ Принимаю условия и продолжаю",
    "sub_check": f"📢 Подписаться на {CHANNEL_ID}",
    "sub_done": "✅ Я подписался",
    "trial": "🎁 Попробовать бесплатно — 1 день",
    "buy": "🛒 Купить подписку",
    "balance": "💰 Баланс",
    "lk": "👤 Личный кабинет",
    "instr": "📖 Инструкции",
    "support": "💬 Поддержка",
    "menu": "🏠 Главное меню",
    "browser": "🌐 Открыть в браузере",
    "backup": "🔗 Резервная ссылка",
    "back": "◀️ Назад",
    "renew": "🔄 Продлить подписку",
}


def kb_agree():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=BTNS["agree"], callback_data="agree"))
    return b.as_markup()


def kb_channel():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=BTNS["sub_check"], url=f"https://t.me/{CHANNEL_ID.replace('@', '')}"))
    b.row(InlineKeyboardButton(text=BTNS["sub_done"], callback_data="check_sub"))
    return b.as_markup()


def kb_main(show_trial: bool = False):
    b = InlineKeyboardBuilder()
    if show_trial:
        b.row(InlineKeyboardButton(text=BTNS["trial"], callback_data="trial"))
    b.row(
        InlineKeyboardButton(text=BTNS["buy"], callback_data="shop"),
        InlineKeyboardButton(text=BTNS["balance"], callback_data="topup"),
    )
    b.row(
        InlineKeyboardButton(text=BTNS["lk"], callback_data="lk"),
        InlineKeyboardButton(text=BTNS["instr"], callback_data="instr"),
    )
    b.row(InlineKeyboardButton(text=BTNS["support"], url=SUPPORT_LINK))
    return b.as_markup()


def kb_trial_after(key: str):
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=BTNS["menu"], callback_data="menu"))
    b.row(InlineKeyboardButton(text=BTNS["lk"], callback_data="lk"))
    b.row(InlineKeyboardButton(text=BTNS["browser"], url=sub_url(key)))
    b.row(InlineKeyboardButton(text=BTNS["backup"], url=sub_url_backup(key)))
    b.row(InlineKeyboardButton(text=BTNS["instr"], callback_data="instr"))
    b.row(InlineKeyboardButton(text=BTNS["buy"], callback_data="shop"))
    return b.as_markup()


def kb_lk(has_sub: bool = False, key: str = None):
    b = InlineKeyboardBuilder()
    if has_sub and key:
        b.row(InlineKeyboardButton(text=BTNS["browser"], url=sub_url(key)))
        b.row(InlineKeyboardButton(text=BTNS["backup"], url=sub_url_backup(key)))
    if has_sub:
        b.row(InlineKeyboardButton(text=BTNS["instr"], callback_data="instr"))
    else:
        b.row(InlineKeyboardButton(text=BTNS["buy"], callback_data="shop"))
    b.row(InlineKeyboardButton(text=BTNS["balance"], callback_data="topup"))
    b.row(InlineKeyboardButton(text=BTNS["menu"], callback_data="menu"))
    return b.as_markup()


def kb_go_lk(key: str = None):
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=BTNS["lk"], callback_data="lk"))
    if key:
        b.row(InlineKeyboardButton(text=BTNS["browser"], url=sub_url(key)))
        b.row(InlineKeyboardButton(text=BTNS["backup"], url=sub_url_backup(key)))
    return b.as_markup()


def kb_shop():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="⚡️ Start", callback_data="buy_start"))
    b.row(InlineKeyboardButton(text="🔥 Plus", callback_data="buy_plus"))
    b.row(InlineKeyboardButton(text="💎 Pro", callback_data="buy_pro"))
    b.row(InlineKeyboardButton(text=BTNS["back"], callback_data="menu"))
    return b.as_markup()


def kb_instr():
    b = InlineKeyboardBuilder()
    platforms = [
        ("📱 Android", "android"), ("🍎 iOS", "ios"),
        ("🖥 Windows", "windows"), ("🍏 macOS", "macos"),
    ]
    for i in range(0, len(platforms), 2):
        b.row(
            InlineKeyboardButton(text=platforms[i][0], callback_data=f"instr_{platforms[i][1]}"),
            InlineKeyboardButton(text=platforms[i + 1][0], callback_data=f"instr_{platforms[i + 1][1]}"),
        )
    b.row(InlineKeyboardButton(text=BTNS["back"], callback_data="lk"))
    return b.as_markup()


def kb_instr_back():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=BTNS["instr"], callback_data="instr"))
    b.row(InlineKeyboardButton(text=BTNS["menu"], callback_data="menu"))
    return b.as_markup()


def kb_activated(key: str):
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=BTNS["menu"], callback_data="menu"))
    b.row(InlineKeyboardButton(text=BTNS["lk"], callback_data="lk"))
    b.row(InlineKeyboardButton(text=BTNS["browser"], url=sub_url(key)))
    b.row(InlineKeyboardButton(text=BTNS["backup"], url=sub_url_backup(key)))
    b.row(InlineKeyboardButton(text=BTNS["instr"], callback_data="instr"))
    return b.as_markup()


def kb_go_shop():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=BTNS["renew"], callback_data="shop"))
    return b.as_markup()


def kb_pay(payment_url: str):
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="💳 Перейти к оплате", url=payment_url))
    b.row(InlineKeyboardButton(text=BTNS["back"], callback_data="menu"))
    return b.as_markup()