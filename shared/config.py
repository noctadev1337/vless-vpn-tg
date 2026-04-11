import os

# Название VPN-сервиса (отображается в дашборде и подписке)
VPN_NAME = "MyVPN"

# База данных
DB_PATH = "/opt/vpn/vpn.db"

# Настройки XUI (Панель управления)
XUI_HOST = "http://127.0.0.1:54321"
XUI_PATH = "/admin_panel"
XUI_USER = "admin"
XUI_PASS = "password"
XUI_INBOUND_ID = 1

# Настройки XUI 2 (Резервный сервер)
XUI2_HOST = "http://0.0.0.0:54321"
XUI2_PATH = "/admin_panel"
XUI2_USER = "admin"
XUI2_PASS = "password"

# Параметры подключения VLESS Reality
DOMAIN = "your-domain.com"
DOMAIN_BACKUP = "res.your-domain.com"
VLESS_PORT = 4443
VLESS_PBK = "YOUR_PUBLIC_KEY"
VLESS_SNI = "google.com"
VLESS_SID = "01"
VLESS_FP = "chrome"

# Платежная система (ЮKassa)
YOOKASSA_SHOP_ID = "000000"
YOOKASSA_SECRET_KEY = "live_xxxxxxxxxxxx"

# Ссылки и бот
BOT_LINK = "https://t.me/your_bot"
PRIVACY_URL = "https://telegra.ph/privacy"
TERMS_URL = "https://telegra.ph/terms"
CHANNEL_ID = "@your_channel"

# Тарифные планы
PLANS = {
    "trial": {
        "name": "🎁 Пробный период",
        "traffic_gb": 150,
        "devices": 3,
        "price": 0,
        "days": 1,
        "hidden": True
    },
    "start": {
        "name": "⚡️ Start",
        "traffic_gb": 150,
        "devices": 3,
        "price": 100,
        "days": 30,
        "hidden": False
    },
    "plus": {
        "name": "🔥 Plus",
        "traffic_gb": 500,
        "devices": 5,
        "price": 169,
        "days": 30,
        "hidden": False
    },
    "pro": {
        "name": "💎 Pro",
        "traffic_gb": 0,
        "devices": 10,
        "price": 299,
        "days": 30,
        "hidden": False
    },
    "black": {
        "name": "🖤 Black",
        "traffic_gb": 0,
        "devices": 5,
        "price": 0,
        "days": 30,
        "hidden": True
    },
}
