import os
from dotenv import load_dotenv

# Загружаем переменные из файла .env, если он есть
load_dotenv()

# КРИТИЧЕСКИЕ ДАННЫЕ (Берем только из окружения)
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_token_here")

# ID администраторов (преобразуем строку из .env в список int)
admin_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(aid.strip()) for aid in admin_raw.split(",") if aid.strip()] or []

# ПУБЛИЧНЫЕ НАСТРОЙКИ
CHANNEL_ID = os.getenv("CHANNEL_ID", "@your_channel")
SUPPORT_LINK = os.getenv("SUPPORT_LINK", "https://t.me/your_support_bot")

# ССЫЛКИ НА ДОКУМЕНТЫ
PRIVACY_URL = "https://telegra.ph/Privacy-Policy-Link"
TERMS_URL = "https://telegra.ph/Terms-of-Service-Link"

# МЕДИА И ПУТИ
# Используем относительные пути или переменные, чтобы код работал на любой машине
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANNER_PATH = os.getenv("BANNER_PATH", os.path.join(BASE_DIR, "assets", "banner.jpg"))
BANNER_URL = os.getenv("BANNER_URL", "https://link-to-your-image.png")

# Для отладки (не забудь выключить в продакшене)
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Telegram-аккаунты бота и поддержки (для сообщений)
BOT_USERNAME = os.getenv("BOT_USERNAME", "@your_vpn_bot")
SUPPORT_BOT = os.getenv("SUPPORT_BOT", "@your_vpn_support_bot")
