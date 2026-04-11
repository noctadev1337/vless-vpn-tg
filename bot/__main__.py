import asyncio
import logging
import os
import aiohttp

# Импорты конфигурации и логики
from bot.config import BANNER_PATH, BANNER_URL, ADMIN_IDS
from bot.instance import bot as bot_instance, dp
from bot.middleware import TrackSourceMiddleware
from shared.database import db_init

# Импорт хендлеров и фоновых задач
import bot.handlers  # noqa: F401
from bot.handlers.tasks import expiry_loop, notify_loop

from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger(__name__)


async def download_assets():
    """Загрузка необходимых медиа-ресурсов при старте."""
    if os.path.exists(BANNER_PATH):
        return
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(BANNER_URL) as response:
                if response.status == 200:
                    os.makedirs(os.path.dirname(BANNER_PATH), exist_ok=True)
                    with open(BANNER_PATH, "wb") as f:
                        f.write(await response.read())
                    log.info("Assets (banner) successfully synchronized.")
    except Exception as e:
        log.warning(f"Asset synchronization failed: {e}")


async def setup_bot_commands():
    """Настройка меню команд для пользователей и администраторов."""

    # Базовые команды для всех
    default_commands = [
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="lk", description="👤 Личный кабинет"),
        BotCommand(command="balance", description="💰 Мой баланс"),
        BotCommand(command="instructions", description="📖 Инструкции"),
        BotCommand(command="help", description="💬 Помощь"),
    ]

    # Расширенный функционал для админ-панели
    admin_commands = [
        BotCommand(command="givesub", description="🎁 Выдать подписку"),
        BotCommand(command="removesub", description="❌ Удалить подписку"),
        BotCommand(command="listsub", description="📋 Список подписок"),
        BotCommand(command="addbalance", description="💳 Пополнить баланс"),
        BotCommand(command="news", description="📢 Рассылка"),
        BotCommand(command="notify", description="📨 Уведомление"),
    ]

    # Установка глобального меню
    await bot_instance.set_my_commands(
        default_commands,
        scope=BotCommandScopeDefault()
    )

    # Персональное меню для каждого ID из списка администраторов
    for admin_id in ADMIN_IDS:
        try:
            await bot_instance.set_my_commands(
                default_commands + admin_commands,
                scope=BotCommandScopeChat(chat_id=admin_id)
            )
        except Exception as e:
            log.debug(f"Could not set commands for admin {admin_id}: {e}")


async def main():
    """Основной цикл запуска бота."""
    # Инициализация ресурсов и БД
    await db_init()

    # Регистрация мидлварей (отслеживание источников и т.д.)
    dp.callback_query.middleware(TrackSourceMiddleware())

    # Подготовка окружения
    await download_assets()
    await setup_bot_commands()

    # Запуск воркеров в фоне (проверки лимитов, уведомления)
    asyncio.create_task(expiry_loop())
    asyncio.create_task(notify_loop())

    log.info("Bot engine started successfully.")

    # Запуск поллинга с игнорированием старых обновлений
    try:
        await dp.start_polling(bot_instance, skip_updates=True)
    finally:
        await bot_instance.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Bot stopped.")
