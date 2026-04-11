from api.config import DOMAIN3, VLESS3_PORT, VLESS3_PBK, VLESS3_SID
from shared.config import DOMAIN, VLESS_PORT, VLESS_PBK, VLESS_FP, VLESS_SNI, VLESS_SID

# Названия для удобства управления из одного места
LOC_DE = "\U0001f1e9\U0001f1ea"  # 🇩🇪
LOC_RU = "\U0001f1f7\U0001f1fa"  # 🇷🇺
ICON_DIR = "\U0001f4f1"  # 📱
ICON_CF = "\U0001f6dc"  # 🛶
ICON_WL = "\U0001f3f3\U0000fe0f"  # 🏳️


def vless_germany_ws_direct(uuid: str) -> str:
    # Используем DOMAIN3 или IP из конфига
    return (f"vless://{uuid}@{DOMAIN3}:{VLESS3_PORT}?type=ws&path=%2Fws-de&host={DOMAIN3}"
            f"&security=tls&sni={DOMAIN3}"
            f"#{LOC_DE}{ICON_DIR} Frankfurt CDN | Direct")


def vless_ws_direct(uuid: str) -> str:
    return (f"vless://{uuid}@{DOMAIN3}:{VLESS3_PORT}?type=ws&path=%2Fws&host={DOMAIN3}"
            f"&security=tls&sni={DOMAIN3}"
            f"#{LOC_RU}{ICON_DIR} Moscow CDN | Direct")


def vless_germany_ws_cf(uuid: str) -> str:
    # Здесь используется основной DOMAIN через Cloudflare
    return (f"vless://{uuid}@{DOMAIN}:443?type=ws&path=%2Fws-de&host={DOMAIN}"
            f"&security=tls&sni={DOMAIN}"
            f"#{LOC_DE}{ICON_CF} Frankfurt CDN | Cloudflare")


def vless_ws_cf(uuid: str) -> str:
    return (f"vless://{uuid}@{DOMAIN}:443?type=ws&path=%2Fws&host={DOMAIN}"
            f"&security=tls&sni={DOMAIN}"
            f"#{LOC_RU}{ICON_CF} Moscow CDN | Cloudflare")


def vless_germany_xhttp(uuid: str) -> str:
    return (f"vless://{uuid}@{DOMAIN3}:{VLESS3_PORT}?type=xhttp&path=%2Fxvk&security=reality"
            f"&pbk={VLESS3_PBK}&fp={VLESS_FP}&sni={VLESS_SNI}&sid={VLESS3_SID}"
            f"#{LOC_DE}{ICON_WL}[\U0001f527] Frankfurt | Whitelist")


def vless_russia_xhttp(uuid: str) -> str:
    return (f"vless://{uuid}@{DOMAIN3}:{VLESS3_PORT}?type=xhttp&path=%2Fxvk&security=reality"
            f"&pbk={VLESS_PBK}&fp={VLESS_FP}&sni={VLESS_SNI}&sid={VLESS_SID}"
            f"#{LOC_RU}{ICON_WL}[\U0001f9ea] Moscow | Whitelist")


def build_subscription(xui_uuid: str, xui_uuid2: str = None) -> str:
    # Список функций для автоматической сборки
    configs = [
        (vless_germany_ws_direct, xui_uuid2),
        (vless_ws_direct, xui_uuid),
        (vless_germany_ws_cf, xui_uuid2),
        (vless_ws_cf, xui_uuid),
        (vless_germany_xhttp, xui_uuid2),
        (vless_russia_xhttp, xui_uuid),
    ]

    links = [func(u) if u else None for func, u in configs]
    return "\n".join(filter(None, links))
