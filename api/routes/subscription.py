import base64
import logging
import asyncio
from datetime import datetime

import aiosqlite
from fastapi import Request
from fastapi.responses import HTMLResponse, Response

from api.config import BROWSER_TOKENS
from api.html import build_html
from api.vless import build_subscription
from bot.config import BOT_USERNAME, SUPPORT_LINK
from shared.config import DB_PATH, DOMAIN, VPN_NAME, BOT_LINK
# Выносим импорты API наверх для скорости
from shared.xui import xui, xui_ws, xui3, get_xui2, get_xui2_ws, get_xui3_de

log = logging.getLogger(__name__)

# Шаблон HTML для истекшей подписки (вынесен для чистоты кода)
EXPIRED_HTML = f"""<!DOCTYPE html><html><head><meta charset=UTF-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>{VPN_NAME}</title>
<style>body{{background:#06030b;color:#f8fafc;font-family:Inter,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}}
.box{{text-align:center;padding:40px 24px}}.emoji{{font-size:3rem;margin-bottom:16px}}
h1{{font-size:1.4rem;margin-bottom:12px}}p{{color:#94a3b8;margin-bottom:24px}}
a{{display:inline-block;background:linear-gradient(135deg,#9333ea,#4f46e5);color:#fff;padding:14px 28px;border-radius:14px;text-decoration:none;font-weight:600}}
</style></head><body><div class=box><div class=emoji>⏳</div><h1>Подписка закончилась</h1>
<p>Продли подписку, чтобы продолжить пользоваться VPN</p>
<a href="{BOT_LINK}">🤖 Продлить в боте</a></div></body></html>"""


def _is_browser(ua: str) -> bool:
    ua_lower = ua.lower()
    return any(t in ua_lower for t in BROWSER_TOKENS)


def _expired_response() -> Response:
    lines = (
        f"vless://00000000-0000-0000-0000-000000000000@0.0.0.0:443?type=tcp&security=none#⏳ Подписка закончилась\n"
        f"vless://00000000-0000-0000-0000-000000000001@0.0.0.0:443?type=tcp&security=none#🤖 Продли в {BOT_USERNAME}"
    )
    encoded = base64.b64encode(lines.encode()).decode()
    title = base64.b64encode("Подписка истекла".encode()).decode()
    return Response(
        content=encoded,
        headers={
            "Content-Type": "text/plain; charset=utf-8",
            "profile-title": f"base64:{title}",
            "profile-update-interval": "1",
            "support-url": SUPPORT_LINK,  # ← теперь из конфига
        },
    )


async def _get_news():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT text, created_at FROM news ORDER BY id DESC LIMIT 1") as c:
                row = await c.fetchone()
                return (row["text"], row["created_at"]) if row else None
    except Exception as e:
        log.error(f"News fetch error: {e}")
    return None


async def _fetch_api_traffic(api, email: str) -> int:
    """Вспомогательная функция для безопасного опроса одного API."""
    try:
        if api:
            t = await api.get_traffic(email)
            return (t.get("up") or 0) + (t.get("down") or 0)
    except Exception:
        pass
    return 0


async def _get_total_traffic(email: str) -> int:
    # Маппинг API и их суффиксов для email
    targets = [
        (xui, ""),  # MSK Reality
        (xui_ws, "_ws"),  # MSK WS
        (xui3, "_xhttp"),  # MSK XHTTP
        (get_xui2(), ""),  # FRA Reality
        (get_xui2_ws(), "_ws"),  # FRA WS
        (get_xui3_de(), "_xhttp")  # FRA XHTTP
    ]

    # Запускаем все запросы параллельно
    tasks = [_fetch_api_traffic(api, email + suffix) for api, suffix in targets]
    results = await asyncio.gather(*tasks)
    return sum(results)


async def subscription_handler(key: str, request: Request):
    if len(key.split("-")) != 3:
        return Response(status_code=404)

    ua = request.headers.get("user-agent", "")

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM subs WHERE key=?", (key,)) as c:
            sub = await c.fetchone()

    if not sub:
        return Response(status_code=404)

    expires = datetime.fromisoformat(str(sub["expires_at"]))
    is_expired = not sub["active"] or expires <= datetime.now()

    if is_expired:
        return HTMLResponse(EXPIRED_HTML) if _is_browser(ua) else _expired_response()

    # Сбор данных
    used_b, news = await asyncio.gather(
        _get_total_traffic(sub["xui_email"]),
        _get_news() if _is_browser(ua) else asyncio.sleep(0, result=None)
    )
    limit_b = sub["traffic_b"]

    if _is_browser(ua):
        return HTMLResponse(build_html(sub, used_b, limit_b, expires, key, tg_id=sub["tg_id"], news=news))

    # Сборка конфигов для клиента (v2ray/Shadowrocket/etc)
    vless_configs = build_subscription(sub["xui_uuid"], sub["xui_uuid2"])
    encoded = base64.b64encode(vless_configs.encode()).decode()
    title = base64.b64encode(VPN_NAME.encode()).decode()

    return Response(
        content=encoded,
        headers={
            "Content-Type": "text/plain; charset=utf-8",
            "profile-title": f"base64:{title}",
            "profile-update-interval": "6",  # Обновление раз в 6 часов достаточно
            "support-url": SUPPORT_LINK,
            "profile-web-page-url": f"https://{DOMAIN}/{key}",
            "subscription-userinfo": f"upload=0; download={used_b}; total={limit_b}; expire={int(expires.timestamp())}",
        },
    )
