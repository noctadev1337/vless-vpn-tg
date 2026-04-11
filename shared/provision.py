import logging
import time
from datetime import datetime, timedelta

from shared.config import PLANS
from shared.database import db_get_sub, db_deactivate, db_create_sub, db_extend_sub
from shared.xui import xui, get_xui2, get_xui2_ws, xui_ws, xui3, get_xui3_de

log = logging.getLogger(__name__)


async def provision_sub(tg_id: int, plan_id: str, days: int):
    """
    Если у пользователя есть активная подписка — продлевает существующий ключ
    (срок прибавляется к текущей дате истечения, UUID и ключ остаются теми же).

    Если подписки нет — создаёт новую с нуля.
    """
    plan = PLANS[plan_id]
    traffic_b = plan["traffic_gb"] * 1024 ** 3 if plan["traffic_gb"] > 0 else 0
    old = await db_get_sub(tg_id)

    if old:
        # ── продление ──────────────────────────────────────────────────────
        old_exp = datetime.fromisoformat(str(old["expires_at"]))
        base = max(old_exp, datetime.now())  # если вдруг истекла, считаем от сегодня
        new_exp = base + timedelta(days=days)
        new_exp_ms = int(new_exp.timestamp() * 1000)

        # обновляем Moscow
        await xui.extend_client(
            old["xui_uuid"], old["xui_email"],
            traffic_b, plan["devices"], new_exp_ms,
        )

        # обновляем WS inbound
        try:
            await xui_ws.extend_client(
                old["xui_uuid"], old["xui_email"] + "_ws",
                traffic_b, plan["devices"], new_exp_ms,
            )
        except Exception as e:
            log.error(f"WS extend_client failed: {e}")

        # обновляем Frankfurt (не блокируем при ошибке)
        if old["xui_uuid2"]:
            try:
                await get_xui2().extend_client(
                    old["xui_uuid2"], old["xui_email"],
                    traffic_b, plan["devices"], new_exp_ms,
                )
            except Exception as e:
                log.error(f"Frankfurt extend_client failed: {e}")
            try:
                await get_xui2_ws().extend_client(
                    old["xui_uuid2"], old["xui_email"] + "_ws",
                    traffic_b, plan["devices"], new_exp_ms,
                )
            except Exception as e:
                log.error(f"Frankfurt WS extend_client failed: {e}")
            try:
                await get_xui3_de().extend_client(
                    old["xui_uuid2"], old["xui_email"] + "_xhttp",
                    traffic_b, plan["devices"], new_exp_ms,
                )
            except Exception as e:
                log.error(f"Frankfurt xhttp extend_client failed: {e}")

        try:
            await xui3.extend_client(
                old["xui_uuid"], old["xui_email"] + "_xhttp",
                traffic_b, plan["devices"], new_exp_ms,
            )
        except Exception as e:
            log.error(f"Moscow xhttp extend_client failed: {e}")

        key, expires_at = await db_extend_sub(tg_id, plan_id, new_exp)
        return key, expires_at

    # ── создание новой подписки ────────────────────────────────────────────
    email = f"tg{tg_id}_{int(time.time())}"
    exp_ms = int((datetime.now() + timedelta(days=days)).timestamp() * 1000)

    xui_uuid = await xui.add_client(email, traffic_b, plan["devices"], exp_ms)

    try:
        await xui_ws.add_client_with_uuid(xui_uuid, email + "_ws", traffic_b, plan["devices"], exp_ms)
    except Exception as e:
        log.error(f"WS add_client failed: {e}")

    xui_uuid2 = None
    try:
        xui_uuid2 = await get_xui2().add_client(email, traffic_b, plan["devices"], exp_ms)
    except Exception as e:
        log.error(f"Frankfurt add_client failed: {e}")
    if xui_uuid2:
        try:
            await get_xui2_ws().add_client_with_uuid(xui_uuid2, email + "_ws", traffic_b, plan["devices"], exp_ms)
        except Exception as e:
            log.error(f"Frankfurt WS add_client failed: {e}")
        try:
            await get_xui3_de().add_client_with_uuid(xui_uuid2, email + "_xhttp", traffic_b, plan["devices"], exp_ms)
        except Exception as e:
            log.error(f"Frankfurt xhttp add_client failed: {e}")

    try:
        await xui3.add_client_with_uuid(xui_uuid, email + "_xhttp", traffic_b, plan["devices"], exp_ms)
    except Exception as e:
        log.error(f"Moscow xhttp add_client failed: {e}")

    key, expires_at = await db_create_sub(
        tg_id, plan_id, xui_uuid, email, days, xui_uuid2=xui_uuid2
    )
    return key, expires_at
