import base64, subprocess, json, asyncio, os
from fastapi import Request
from fastapi.responses import Response

# Импорт только необходимых констант
from shared.config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY
from shared.database import db_get_topup, db_mark_topup_done, db_add_balance
from bot.config import BOT_TOKEN, BANNER_PATH

# Настройки оформления
YOOKASSA_API_URL = "https://api.yookassa.ru/v3/payments"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


async def webhook_handler(request: Request):
    try:
        data = await request.json()
        payment_obj = data.get("object", {})
        pid = payment_obj.get("id")

        if not pid:
            return Response(status_code=200)

        topup = await db_get_topup(pid)

        # Проверяем только ожидающие платежи
        if topup and topup["status"] == "pending":
            # Запрос статуса через curl + proxychains (если сервер под санкциями/блокировками)
            check_cmd = [
                "proxychains4", "curl", "-s", "-u", f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}",
                f"{YOOKASSA_API_URL}/{pid}"
            ]

            result = subprocess.check_output(check_cmd).decode()
            res_json = json.loads(result)

            # Проверяем финальный статус в ЮKassa
            if res_json.get("status") == "succeeded":
                amount = int(topup["amount"])
                tg_id = topup["tg_id"]

                # Обновляем баланс в БД
                new_bal = await db_add_balance(tg_id, amount)
                await db_mark_topup_done(pid)

                # Формируем красивое уведомление
                caption = (
                    f"✨ <b>Баланс пополнен!</b>\n\n"
                    f"Сумма: <b>{amount} ₽</b>\n"
                    f"Итого на счету: <b>{new_bal} ₽</b>\n\n"
                    f"Приятного пользования! 💜"
                )

                reply_markup = json.dumps({
                    "inline_keyboard": [[
                        {"text": "📱 В меню баланса", "callback_data": "topup"}
                    ]]
                })

                # Отправка уведомления через curl (фоновый процесс)
                # Используем системный curl, чтобы избежать проблем с SSL-библиотеками Python через прокси
                tg_notify_cmd = [
                    "proxychains4", "curl", "-s", "-X", "POST",
                    f"{TELEGRAM_API_URL}/sendPhoto",
                    "-F", f"chat_id={tg_id}",
                    "-F", f"photo=@{BANNER_PATH}",
                    "-F", f"caption={caption}",
                    "-F", "parse_mode=HTML",
                    "-F", f"reply_markup={reply_markup}"
                ]

                subprocess.Popen(
                    tg_notify_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

    except Exception as e:
        # Логирование ошибок в системный журнал
        print(f"[WEBHOOK ERROR]: {e}")

    # Всегда возвращаем 200, чтобы ЮKassa не слала повторы при внутренних ошибках бота
    return Response(status_code=200)
