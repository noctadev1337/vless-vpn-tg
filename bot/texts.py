from datetime import datetime
from html import escape

from bot.config import PRIVACY_URL, TERMS_URL, CHANNEL_ID
from bot.utils import sub_url, sub_url_backup, fmt_traffic
from shared.config import PLANS

APP_PRIMARY = "Happ"
APP_SECONDARY = "v2rayTUN"


def _esc(name: str) -> str:
    return escape(name)


def _fmt_keys(key: str) -> str:
    return (
        f"🔗 <b>Основной ключ:</b>\n"
        f"<code>{sub_url(key)}</code>\n\n"
        f"🔗 <b>Резервный ключ:</b>\n"
        f"<code>{sub_url_backup(key)}</code>"
    )


def t_agree(name: str) -> str:
    return (
        f"👋 Привет, <b>{_esc(name)}</b>!\n\n"
        f"Перед началом работы ознакомься с документами:\n\n"
        f"📄 <a href='{PRIVACY_URL}'>Политика конфиденциальности</a>\n"
        f"📋 <a href='{TERMS_URL}'>Пользовательское соглашение</a>\n\n"
        f"<blockquote>🔒 Мы гарантируем приватность и не передаём ваши данные третьим лицам.\n\n"
        f"Используются только выделенные серверы с высокой доступностью.</blockquote>\n\n"
        f"Нажми кнопку ниже, чтобы продолжить."
    )


def t_channel() -> str:
    return (
        f"📢 <b>Почти готово</b>\n\n"
        f"Подпишись на наш канал <b>{CHANNEL_ID}</b>, чтобы следить за статусом серверов и обновлениями.\n\n"
        f"После подписки нажми кнопку ниже 👇"
    )


def t_welcome(name: str) -> str:
    return (
        f"👋 Привет, <b>{_esc(name)}</b>!\n\n"
        f"Добро пожаловать в сервис безопасного доступа.\n\n"
        f"<blockquote>🛡 Полная анонимность\n"
        f"📱 Поддержка всех ОС\n"
        f"⚡️ Максимальная скорость</blockquote>\n\n"
        f"Выбери действие 👇"
    )


def t_trial_activated(key: str) -> str:
    return (
        f"🎁 <b>Тестовый период активен!</b>\n\n"
        f"{_fmt_keys(key)}\n\n"
        f"<blockquote>"
        f"📊 Трафик — <b>150 ГБ</b>\n"
        f"⏳ Срок — <b>1 день</b>"
        f"</blockquote>\n\n"
        f"<b>Инструкция:</b>\n"
        f"1. Установи <b>{APP_PRIMARY}</b>\n"
        f"2. Нажми <b>＋ → Импорт из буфера</b>\n"
        f"3. Вставь ключ и подключайся ✅"
    )


def t_activated(plan_id: str, key: str, expires: datetime, days: int) -> str:
    p = PLANS.get(plan_id, {})
    tr = "∞ ГБ" if p.get("traffic_gb", 0) == 0 else f"{p['traffic_gb']} ГБ"
    return (
        f"🚀 <b>Подписка активирована!</b>\n\n"
        f"{_fmt_keys(key)}\n\n"
        f"<blockquote>"
        f"📦 Тариф — <b>{p.get('name', plan_id)}</b>\n"
        f"📊 Трафик — <b>{tr}</b>\n"
        f"📱 Устройств — <b>{p.get('devices', '—')}</b>\n"
        f"📅 Истекает — <b>{expires.strftime('%d.%m.%Y')}</b>\n"
        f"⏳ Срок — <b>{days} дн.</b>"
        f"</blockquote>\n\n"
        f"<b>Как подключиться:</b>\n"
        f"1. Установи <b>{APP_PRIMARY}</b>\n"
        f"2. Нажми <b>＋ → Импорт из буфера</b>\n"
        f"3. Вставь ключ и подключайся ✅"
    )


def t_shop(has_sub: bool, sub=None, balance: int = 0) -> str:
    if has_sub and sub:
        p = PLANS.get(sub["plan"], {"name": sub["plan"]})
        exp = datetime.fromisoformat(str(sub["expires_at"]))
        days_left = max(0, (exp - datetime.now()).days)
        return (
            f"🛒 <b>Тарифы</b>\n\n"
            f"У вас есть активная подписка:\n"
            f"<blockquote>📦 Тариф: <b>{p['name']}</b>\n"
            f"⏳ Осталось: <b>{days_left} дн.</b></blockquote>\n\n"
            f"Покупка нового периода добавится к текущему сроку."
        )
    return (
        f"🛒 <b>Доступные тарифы</b>\n\n"
        f"<blockquote>"
        f"⚡️ <b>Start</b>  · 100 ₽ · 150 ГБ\n"
        f"🔥 <b>Plus</b>   · 169 ₽ · 500 ГБ\n"
        f"💎 <b>Pro</b>    · 299 ₽ · ∞ ГБ"
        f"</blockquote>\n\n"
        f"💰 Твой баланс: <b>{balance} ₽</b>\n"
        f"🚀 Выдача доступа происходит мгновенно."
    )


def t_lk(sub, traffic=None, balance: int = 0) -> str:
    if not sub:
        return (
            f"👤 <b>Личный кабинет</b>\n\n"
            f"Баланс: <b>{balance} ₽</b>\n\n"
            f"У вас пока нет активных подключений.\n"
            f"Выберите тариф в магазине для начала работы."
        )
    p = PLANS.get(sub["plan"], {"name": sub["plan"]})
    exp = datetime.fromisoformat(str(sub["expires_at"]))
    tr = traffic or {}
    used_b = (tr.get("up") or 0) + (tr.get("down") or 0)
    tr_str = fmt_traffic(used_b, sub["traffic_b"])
    return (
        f"👤 <b>Личный кабинет</b>\n\n"
        f"{_fmt_keys(sub['key'])}\n\n"
        f"<blockquote>"
        f"📦 Тариф — <b>{p['name']}</b>\n"
        f"📊 Трафик — <b>{tr_str}</b>\n"
        f"📅 До: <b>{exp.strftime('%d.%m.%Y')}</b>\n"
        f"💰 Баланс: <b>{balance} ₽</b>"
        f"</blockquote>"
    )


INSTR_TPL = (
    "1. Скачай клиент <b>{app}</b>\n"
    "2. Нажми <b>＋ → Импорт из буфера</b>\n"
    "3. Вставь ключ из личного кабинета\n"
    "4. Нажми кнопку подключения ✅"
)

INSTR = {
    "android": f"📱 <b>Android — {APP_PRIMARY} / {APP_SECONDARY}</b>\n\n" + INSTR_TPL.format(app=APP_PRIMARY),
    "ios": f"🍎 <b>iOS — {APP_PRIMARY}</b>\n\n" + INSTR_TPL.format(app=APP_PRIMARY),
    "windows": f"🖥 <b>Windows — {APP_PRIMARY}</b>\n\n" + INSTR_TPL.format(app=APP_PRIMARY),
}
INSTR["macos"] = INSTR["windows"].replace("🖥 Windows", "🍏 macOS")