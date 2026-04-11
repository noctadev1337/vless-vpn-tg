import asyncio
import logging

from bot.keyboards import kb_go_shop
from bot.utils import send
from shared.config import PLANS
from shared.database import (
    db_deactivate, db_get_expired,
    db_get_subs_for_notify, db_set_notified,
)
from shared.xui import xui, get_xui2, get_xui2_ws, xui_ws

log = logging.getLogger(__name__)

# (часов до истечения, бит в маске, человекочитаемый текст)
NOTIFY_SCHEDULE = [
    (24, 1, "24 часа"),
    (12, 2, "12 часов"),
    (6, 4, "6 часов"),
    (3, 8, "3 часа"),
    (1, 16, "1 час"),
]


async def expiry_loop():
    """Деактивирует истёкшие подписки и уведомляет пользователей."""
    while True:
        try:
            for s in await db_get_expired():
                try:
                    await xui.delete_client(s["xui_uuid"])
                except Exception as e:
                    log.warning(f"expiry delete Moscow {s['tg_id']}: {e}")

                if s["xui_uuid2"]:
                    try:
                        await get_xui2().delete_client(s["xui_uuid2"])
                    except Exception as e:
                        log.warning(f"expiry delete Frankfurt {s['tg_id']}: {e}")

                try:
                    await xui_ws.delete_client(s["xui_uuid"])
                except Exception as e:
                    log.warning(f"expiry delete WS {s['tg_id']}: {e}")
                if s["xui_uuid2"]:
                    try:
                        await get_xui2_ws().delete_client(s["xui_uuid2"])
                    except Exception as e:
                        log.warning(f"expiry delete Frankfurt WS {s['tg_id']}: {e}")

                await db_deactivate(s["tg_id"])

                try:
                    await send(
                        s["tg_id"],
                        (
                            f"⚠️ <b>Подписка закончилась!</b>\n\n"
                            f"Тариф <b>{PLANS.get(s['plan'], {}).get('name', s['plan'])}</b> истёк.\n"
                            f"VPN-ключ деактивирован.\n\n"
                            f"Продли подписку, чтобы продолжить 🔄"
                        ),
                        kb_go_shop(),
                    )
                except Exception as e:
                    log.warning(f"expiry notify {s['tg_id']}: {e}")
        except Exception as e:
            log.error(f"expiry_loop: {e}")

        await asyncio.sleep(3600)


async def notify_loop():
    """Отправляет уведомления об истечении подписки за 24/12/6/3/1 час."""
    while True:
        try:
            for hours, bit, label in NOTIFY_SCHEDULE:
                subs = await db_get_subs_for_notify(hours, bit)
                for s in subs:
                    plan_name = PLANS.get(s["plan"], {}).get("name", s["plan"])
                    try:
                        await send(
                            s["tg_id"],
                            (
                                f"⏳ <b>Подписка истекает через {label}!</b>\n\n"
                                f"Тариф: <b>{plan_name}</b>\n\n"
                                f"Не потеряй доступ — продли прямо сейчас 👇"
                            ),
                            kb_go_shop(),
                        )
                        # выставляем бит — больше не отправлять это уведомление
                        current = s["notified"] if s["notified"] is not None else 0
                        await db_set_notified(s["id"], current | bit)
                    except Exception as e:
                        log.warning(f"notify {s['tg_id']} ({label}): {e}")
        except Exception as e:
            log.error(f"notify_loop: {e}")

        await asyncio.sleep(600)  # проверяем каждые 10 минут
