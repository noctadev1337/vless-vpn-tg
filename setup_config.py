#!/usr/bin/env python3
"""
Скрипт настройки конфигурации Vless VPN (Telegram Bot + API).
1. Заполняет конфиги (shared, api, .env).
2. Удаляет старую БД для чистого запуска.
"""

import os
import re
import shutil


def read_input(prompt: str, default: str = None, required: bool = True) -> str:
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    while True:
        value = input(prompt).strip()
        if value:
            return value
        if default:
            return default
        if not required:
            return ""
        print("Это поле обязательно для заполнения.")


def read_int(prompt: str, default: int = None) -> int:
    while True:
        value = read_input(prompt, str(default) if default else None)
        try:
            return int(value)
        except ValueError:
            print("Введите число.")


def update_file(filepath: str, replacements: dict):
    if not os.path.exists(filepath):
        print(f"   ⚠️ Файл не найден: {filepath}")
        return
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    for pattern, value in replacements.items():
        # Замена для строк: KEY = "value"
        content = re.sub(rf'({re.escape(pattern)}\s*=\s*)"[^"]*"', f'\\1"{value}"', content)
        # Замена для чисел: KEY = 123
        content = re.sub(rf'({re.escape(pattern)}\s*=\s*)\d+', f'\\1{value}', content)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"   ✅ Обновлено: {filepath}")


def main():
    print("=" * 50)
    print("   Vless VPN - Интерактивная настройка")
    print("=" * 50)

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # [1] ОСНОВНЫЕ ПАРАМЕТРЫ
    print("\n[1/4] Основные параметры")
    vpn_name = read_input("Название сервиса", "My Vless VPN")
    bot_link = read_input("Ссылка на бота", "https://t.me/my_vless_bot")
    channel = read_input("ID канала (подписка)", "@my_channel")
    support = read_input("Поддержка", "https://t.me/support_bot")
    db_path = read_input("Путь к vpn.db (абсолютный или относительный)", "vpn.db")

    # [2] ОСНОВНОЙ СЕРВЕР (shared/config.py)
    print("\n[2/4] Основной сервер (3x-UI)")
    x_host = read_input("Хост (http://IP:PORT)", "http://127.0.0.1:54321")
    x_path = read_input("Секретный путь панели", "/login")
    x_user = read_input("Логин панели")
    x_pass = read_input("Пароль панели")
    x_inbound = read_int("ID Reality Inbound", 1)

    domain = read_input("Основной домен (CF Proxied)")
    domain_res = read_input("Резервный домен (DNS Only)", domain)

    shared_replacements = {
        "VPN_NAME": vpn_name, "BOT_LINK": bot_link, "CHANNEL_ID": channel,
        "DB_PATH": db_path, "XUI_HOST": x_host, "XUI_PATH": x_path,
        "XUI_USER": x_user, "XUI_PASS": x_pass, "XUI_INBOUND_ID": x_inbound,
        "DOMAIN": domain, "DOMAIN_BACKUP": domain_res
    }

    # [3] РЕЗЕРВНЫЙ СЕРВЕР (api/config.py)
    print("\n[3/4] Дополнительный сервер (если есть)")
    x2_host = read_input("Хост 2-го сервера", "http://0.0.0.0:54321", required=False)

    api_replacements = {}
    if x2_host and x2_host != "http://0.0.0.0:54321":
        api_replacements = {
            "XUI2_HOST": x2_host,
            "XUI2_USER": read_input("Логин 2"),
            "XUI2_PASS": read_input("Пароль 2"),
            "XUI2_INBOUND_ID": read_int("ID Reality Inbound 2", 1)
        }

    # [4] ENV & BOT
    print("\n[4/4] Telegram Bot & Security")
    token = read_input("Bot Token (из BotFather)")
    admins = read_input("Admin IDs (через запятую)", "123456789")

    # Сборка .env
    env_content = f"""BOT_TOKEN={token}
ADMIN_IDS={admins}
CHANNEL_ID={channel}
SUPPORT_LINK={support}
DB_PATH={db_path}
DEBUG=False
"""

    # ПРИМЕНЕНИЕ
    print("\n" + "-" * 30)
    update_file(os.path.join(base_dir, "shared", "config.py"), shared_replacements)
    if api_replacements:
        update_file(os.path.join(base_dir, "api", "config.py"), api_replacements)

    with open(os.path.join(base_dir, ".env"), "w", encoding="utf-8") as f:
        f.write(env_content)
    print("   ✅ Создан .env")

    # УДАЛЕНИЕ СТАРОЙ БАЗЫ
    full_db_path = db_path if os.path.isabs(db_path) else os.path.join(base_dir, db_path)
    if os.path.exists(full_db_path):
        try:
            os.remove(full_db_path)
            print(f"   🔥 Старая база {db_path} удалена для чистого запуска.")
        except Exception as e:
            print(f"   ⚠️ Не удалось удалить БД: {e}")

    print("-" * 30)
    print("\n🚀 Настройка завершена!")
    print("Теперь запустите API и Бот:")
    print("1. python -m api")
    print("2. python -m bot")


if __name__ == "__main__":
    main()
