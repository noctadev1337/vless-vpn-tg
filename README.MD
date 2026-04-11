# Vless VPN (Telegram Bot + API)

> ⚠️ **Тестовый репозиторий** — данный репозиторий предоставляется как есть, без гарантий работоспособности. Используйте для
> изучения архитектуры и локального тестирования. При настройке могут произойти ошибки.

Селф-хостед VLESS VPN сервис с Telegram-ботом, мультисерверной поддержкой, системой баланса и интеграцией платежей.

Стек: **3x-ui** + **aiogram 3** + **FastAPI** + **SQLite**

---

## Быстрый старт

```bash
# 1. Клонирование
git clone https://github.com/noctadev1337/vless-vpn-tg.git
cd vless-vpn-tg

# 2. Виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. Зависимости
pip install -r requirements.txt

# 4. Интерактивная настройка
python setup_config.py
```

Скрипт `setup_config.py` запросит:

- Название VPN-сервиса
- Параметры Telegram-бота
- Данные 3x-UI панелей (основной + резервный сервер)
- VLESS Reality ключи
- ЮKassa (опционально)

После настройки:

```bash
# 5. Запуск API (терминал 1)
python -m api

# 6. Запуск бота (терминал 2)
python -m bot
```

---

## Принцип работы

```
                        ┌─────────────────────────────────────────────┐
                        │              Пользователь                   │
                        └──────────┬──────────────────┬───────────────┘
                                   │                  │
                          Telegram Bot           Клиент VPN
                          (покупка,              (Happ, v2rayTUN)
                          управление)                 │
                                   │                  │
                    ┌──────────────▼──┐        ┌──────▼──────────────┐
                    │   aiogram 3     │        │   your-domain.com   │
                    │   Telegram Bot  │        │   Cloudflare CDN    │
                    └──────┬──────┬───┘        └──────────┬──────────┘
                           │      │                       │
                    SOCKS5 │      │ provision             │ 443 (TLS)
                   туннель │      │ (создать/             │
                  (если РКН│      │  продлить)      ┌─────▼──────────────────┐
                  блокирует│      │                 │        nginx           │
                           │      │                 │   SNI-роутинг :443     │
                    ┌──────▼─┐    │                 └──┬──────────┬──────────┘
                    │ Сервер │    │                    │          │
                    │   N    │    │              stream│     http2│
                    │(socks5)│    │           (Reality)│   (API+WS│:8443)
                    └────────┘    │                    │          │
                                  │           ┌────────▼──┐  ┌────▼───────┐
                    ┌─────────────▼──────┐    │  3x-ui    │  │  FastAPI   │
                    │     SQLite DB      │    │  серверы  │  │    :8080   │
                    │  users/subs/topups │    │           │  └─────┬──────┘
                    └────────────────────┘    │ Сервер 1  │        │
                                              │ Сервер 2  │  ┌─────▼──────┐
                    ┌───────────────────┐     │ Сервер N  │  │  Webhook   │
                    │     ЮКасса        │     └───────────┘  │  /payment  │
                    │  СБП-платежи      ├───────────────────►│            │
                    └───────────────────┘                    └────────────┘
```

### Потоки данных

**Покупка подписки:**
Пользователь → Бот → списание с баланса → `provision_sub()` → создание клиента на всех серверах → выдача ключа

**Пополнение баланса:**
Пользователь → Бот → ЮКасса (СБП) → webhook → зачисление на баланс → уведомление в бот

**VPN-подключение:**
Клиент → `your-domain.com:443` → nginx → по SNI либо в 3x-ui (Reality/xHTTP) либо через HTTP в WS inbound

**Подписка как файл:**
Клиент (Happ) → `GET /key` с UA → FastAPI → base64 список VLESS-ссылок всех серверов

**Браузер:**
`GET /key` без VPN-UA → FastAPI → HTML дашборд (трафик, срок, ключ, новости)

---

## Возможности

- Telegram-бот с полным жизненным циклом подписки — покупка, продление, пробный период
- Внутренний баланс с пополнением через ЮКасса (СБП)
- Мультисерверность — добавляй любое количество 3x-ui нод
- Несколько транспортов на каждом сервере: **Reality**, **WebSocket (CDN)**, **xHTTP (Whitelist)**
- Один UUID на сервер, используется во всех inbound (Reality / WS / xHTTP)
- Автоматическая деактивация истёкших подписок
- Уведомления об истечении: за 24ч / 12ч / 6ч / 3ч / 1ч (битмаска)
- Браузерный дашборд по ключу подписки
- Админ-панель через команды бота

---

## Структура проекта

```
/opt/vpn/
├── api/
│   ├── __init__.py          # Делает папку модулем
│   ├── __main__.py          # Запуск FastAPI (uvicorn)
│   ├── config.py            # Конфиг доп. серверов и VLESS параметры
│   ├── html.py              # Генерация дашборда подписки
│   ├── vless.py             # Ссылки vless:// и подписки
│   └── routes/
│       ├── __init__.py
│       ├── subscription.py  # Эндпоинт выдачи подписки
│       └── webhook.py       # Обработка платежей ЮKassa
├── bot/
│   ├── __init__.py
│   ├── __main__.py          # Точка входа aiogram
│   ├── config.py            # Настройки бота и пути
│   ├── instance.py          # Объекты Bot и Dispatcher
│   ├── keyboards.py         # Кнопки меню
│   ├── middleware.py        # Обработка входящих данных
│   ├── texts.py             # Все текстовые сообщения
│   ├── utils.py             # Вспомогательные функции
│   └── handlers/
│       ├── __init__.py
│       ├── admin.py         # Админ-команды
│       ├── instructions.py  # Гайды по настройке
│       ├── lk.py            # Личный кабинет
│       ├── onboarding.py    # Приветствие и регистрация
│       ├── shop.py          # Магазин тарифов
│       ├── tasks.py         # Фоновые проверки истечения
│       └── topup.py         # Оплата баланса
├── shared/
│   ├── __init__.py
│   ├── config.py            # Основные настройки и тарифы
│   ├── database.py          # Работа с SQLite (async)
│   ├── provision.py         # Логика создания/продления в 3x-ui
│   └── xui.py               # API-клиент для панелей 3x-ui
├── .env                     # Секретные ключи (создается через setup_config)
├── .env.example             # Пример шаблона переменных окружения
├── .gitignore               # Исключения для Git
├── banner.jpg               # Изображение для приветствия в боте
├── LICENSE                  # Текст лицензии MIT
├── README.md                # Инструкция и описание
├── requirements.txt         # Список зависимостей (pip install)
├── setup_config.py          # Скрипт первичной настройки (наш новый файл)
└── vpn.db                   # Файл базы данных (создается автоматически)
```

---

## Конфигурация

### shared/config.py — основной сервер и тарифы

```python
DB_PATH = "/opt/vpn/vpn.db"

# Основной сервер (edge, на нём же бот и API)
XUI_HOST = "http://127.0.0.1:54321"
XUI_PATH = "/YOUR_SECRET_PATH"
XUI_USER = "your_xui_login"
XUI_PASS = "your_xui_password"
XUI_INBOUND_ID = 1  # Reality inbound

DOMAIN = "your-domain.com"  # основной ключ (CF proxied)
DOMAIN_BACKUP = "res.your-domain.com"  # резервный ключ (DNS only, прямой IP)

YOOKASSA_SHOP_ID = "YOUR_SHOP_ID"
YOOKASSA_SECRET_KEY = "YOUR_SECRET_KEY"

PLANS = {
    "trial": {"name": "Пробный период", "traffic_gb": 10, "devices": 1, "price": 0, "days": 1, "hidden": True},
    "start": {"name": "Start", "traffic_gb": 150, "devices": 3, "price": 100, "days": 30, "hidden": False},
    "plus": {"name": "Plus", "traffic_gb": 500, "devices": 5, "price": 169, "days": 30, "hidden": False},
    "pro": {"name": "Pro", "traffic_gb": 0, "devices": 10, "price": 299, "days": 30, "hidden": False},
}
```

### bot/config.py

```python
BOT_TOKEN = "YOUR_BOT_TOKEN"
ADMIN_IDS = [123456789]  # Telegram ID администраторов
CHANNEL_ID = "@your_channel"  # Обязательная подписка на канал
SUPPORT_LINK = "https://t.me/your_support_bot"
BANNER_PATH = "/opt/vpn/banner.jpg"
BANNER_URL = "https://fallback-url-to-banner.jpg"
```

### api/config.py — дополнительные серверы

Каждый дополнительный сервер описывается блоком из хоста, пути, логина, пароля и ID inbound:

```python
# Сервер 2 (например, Frankfurt)
XUI2_HOST = "http://YOUR_SERVER_2_IP:54321"  # ⚠️ HTTP, не HTTPS
XUI2_PATH = "/YOUR_SECRET_PATH_2"
XUI2_USER = "your_login_2"
XUI2_PASS = "your_password_2"
XUI2_INBOUND_ID = 1  # Reality inbound
XUI2_WS_INBOUND_ID = 2  # WebSocket inbound

# Сервер 3 — добавляется аналогично
XUI3_HOST = "http://YOUR_SERVER_3_IP:54321"
# ...
```

Инстансы в `shared/xui.py`:

```python
# Основной сервер — три inbound
xui = XUI(XUI_HOST, XUI_PATH, XUI_USER, XUI_PASS, 1)  # Reality
xui_ws = XUI(XUI_HOST, XUI_PATH, XUI_USER, XUI_PASS, 2)  # WebSocket
xui3 = XUI(XUI_HOST, XUI_PATH, XUI_USER, XUI_PASS, 3)  # xHTTP Whitelist


# Дополнительные серверы — lazy init через функции
def get_xui2():     ...  # Reality, сервер 2


def get_xui2_ws():  ...  # WS, сервер 2


def get_xui3_de():  ...  # xHTTP, сервер 2
# get_xui_N() — добавляй сколько нужно
```

---

## Архитектура серверов

### Основной сервер (edge)

На нём живёт всё: бот, API, nginx, 3x-ui, БД.

Если исходящий трафик к `api.telegram.org` заблокирован — бот запускается через `proxychains4` + SOCKS5-туннель на один
из дополнительных серверов:

```ini
# /etc/systemd/system/tg-tunnel.service
[Service]
ExecStart = autossh -M 0 -N -D 127.0.0.1:1080 \
            -i /root/.ssh/server2_key \
            -o StrictHostKeyChecking=no \
            -o ServerAliveInterval=30 \
            root@YOUR_SERVER_2_IP
Restart = always
```

```ini
# /etc/proxychains4.conf
strict_chain
proxy_dns
localnet 127.0.0.0/255.0.0.0   # обязательно — иначе 3x-ui (127.0.0.1) пойдёт через socks5

[ProxyList]
socks5 127.0.0.1 1080
```

### Дополнительные серверы

На каждом — только 3x-ui. Количество не ограничено — добавляй новый сервер в `api/config.py`, создавай инстанс в
`shared/xui.py` и регистрируй его в `shared/provision.py`.

---

## Nginx — SNI-роутинг

Весь трафик на порту 443 разруливается через `stream` по SNI:

```nginx
# Установи модуль: apt install libnginx-mod-stream

stream {
    map $ssl_preread_server_name $backend {
        # Reality — SNI попадает напрямую в 3x-ui
        your-sni-1.com          127.0.0.1:4443;                # сервер 1 Reality
        your-sni-2.com          YOUR_SERVER_2_IP:36357;        # сервер 2 Reality
        your-whitelist-sni.com  127.0.0.1:4446;                # xHTTP Whitelist

        # Домены сервиса — уходят в nginx HTTP
        your-domain.com         127.0.0.1:8443;
        res.your-domain.com     127.0.0.1:8443;
        default                 127.0.0.1:8443;
    }
    server {
        listen 443; listen [::]:443;
        proxy_pass $backend;
        ssl_preread on;
    }
}
```

HTTP-блоки слушают на `127.0.0.1:8443` (не на 443 — он занят stream):

```nginx
http {
    server {
        listen 127.0.0.1:8443 ssl http2;
        server_name your-domain.com;
        ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

        location /      { proxy_pass http://127.0.0.1:8080; }        # API
        location /ws    { proxy_pass http://127.0.0.1:8388; }        # WS сервер 1
        location /ws-2  { proxy_pass http://SERVER_2_IP:8388; }      # WS сервер 2
        # Добавляй /ws-N для каждого дополнительного сервера
    }

    # Резервный домен (DNS only, прямой IP — не блокируется мобильными операторами)
    server {
        listen 127.0.0.1:8443 ssl http2;
        server_name res.your-domain.com;
        ssl_certificate /etc/letsencrypt/live/res.your-domain.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/res.your-domain.com/privkey.pem;
        # аналогичные location
    }
}
```

> **Про Cloudflare:** основной домен — проксируй через CF (оранжевое облако), для вебхука и WS CDN. Резервный домен (
`res.`) — DNS only, прямой IP. CF IP блокируется у части мобильных операторов, поэтому резервный ключ идёт в обход.

---

## 3x-ui — настройка inbound

На каждом сервере рекомендуется три inbound:

| # | Транспорт | Порт  | Security        | Описание                   |
|---|-----------|-------|-----------------|----------------------------|
| 1 | TCP       | любой | Reality         | Основной, работает везде   |
| 2 | WebSocket | 8388  | TLS через nginx | CDN, через Cloudflare      |
| 3 | xHTTP     | любой | Reality         | Whitelist-режим, обход DPI |

> Панель 3x-ui слушает на HTTP. Chrome/Firefox блокируют нестандартные порты — пробрасывай через SSH:
> ```bash
> ssh -L 9000:127.0.0.1:54321 root@YOUR_SERVER_IP -N
> # открывай http://127.0.0.1:9000/YOUR_SECRET_PATH/
> ```

---

## Подписка — что получает пользователь

`build_subscription()` генерирует VLESS-ссылки для всех серверов и транспортов. Чем больше серверов — тем больше строк в
подписке. Клиент (Happ, v2rayTUN) сам выбирает рабочий.

Пример для двух серверов — 6 ссылок:

```
Сервер 1 WS | Direct      — прямой IP:443, ws
Сервер 2 WS | Direct      — прямой IP:443, ws
Сервер 1 WS | Cloudflare  — your-domain.com:443, ws
Сервер 2 WS | Cloudflare  — your-domain.com:443, ws
Сервер 1    | Whitelist   — прямой IP:443, xhttp, Reality
Сервер 2    | Whitelist   — прямой IP:443, xhttp, Reality
```

---

## База данных

```sql
CREATE TABLE subs
(
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id      INTEGER     NOT NULL,
    plan       TEXT        NOT NULL,
    key        TEXT UNIQUE NOT NULL,
    xui_uuid   TEXT        NOT NULL, -- UUID на сервере 1
    xui_uuid2  TEXT,                 -- UUID на сервере 2 (NULL если не добавлен)
    xui_email  TEXT        NOT NULL,
    traffic_b  INTEGER DEFAULT 0,
    devices    INTEGER DEFAULT 3,
    expires_at TEXT        NOT NULL,
    active     INTEGER DEFAULT 1,
    notified   INTEGER DEFAULT 0,    -- битмаска отправленных уведомлений
    created_at TEXT    DEFAULT (datetime('now'))
);
```

Один UUID на сервер — используется во всех его inbound. Email суффиксы разделяют inbound:

- Reality → `email`
- WebSocket → `email_ws`
- xHTTP → `email_xhttp`

---

## Логика provision_sub()

**Новая подписка:**

1. Создаём клиента на каждом сервере через `xui.add_client()`
2. Для каждого inbound — `add_client_with_uuid()` с тем же UUID
3. Сохраняем UUID в БД

**Продление:**

- Берём текущую дату истечения, прибавляем дни
- `extend_client()` на всех inbound всех серверов
- Обновляем запись в БД, сбрасываем `notified = 0`

**Добавление нового сервера к существующим пользователям:**

- При продлении, если `xui_uuid2 IS NULL` — создаём клиента на новом сервере впервые и записываем UUID в БД

---

## Уведомления об истечении

`notify_loop` проверяет раз в 10 минут. `notified` — битмаска:

| Бит | Значение | За сколько |
|-----|----------|------------|
| 0   | 1        | 24 часа    |
| 1   | 2        | 12 часов   |
| 2   | 4        | 6 часов    |
| 3   | 8        | 3 часа     |
| 4   | 16       | 1 час      |

При продлении `notified` сбрасывается в 0.

---

## Systemd-сервисы

```ini
# /etc/systemd/system/vpn-bot.service
[Unit]
Description = VPN Telegram Bot
After = network.target tg-tunnel.service

[Service]
WorkingDirectory = /opt/vpn
ExecStart = proxychains4 /opt/vpn/venv/bin/python -m bot
Environment = "PYTHONPATH=/opt/vpn"
Restart = always
RestartSec = 5

[Install]
WantedBy = multi-user.target
```

```ini
# /etc/systemd/system/vpn-api.service
[Unit]
Description = VPN FastAPI
After = network.target

[Service]
WorkingDirectory = /opt/vpn
ExecStart = /opt/vpn/venv/bin/python -m uvicorn api.__main__:app --host 127.0.0.1 --port 8080
Environment = "PYTHONPATH=/opt/vpn"
Restart = always

[Install]
WantedBy = multi-user.target
```

---

## Команды бота

### Для пользователей

| Команда         | Описание                       |
|-----------------|--------------------------------|
| `/start`        | Главное меню                   |
| `/lk`           | Личный кабинет и ключ подписки |
| `/balance`      | Баланс и пополнение            |
| `/instructions` | Инструкции по подключению      |

### Для администраторов

| Команда                       | Описание                                       |
|-------------------------------|------------------------------------------------|
| `/givesub {id} {plan} {days}` | Выдать подписку                                |
| `/removesub {id}`             | Удалить подписку                               |
| `/listsub`                    | Список активных подписок                       |
| `/addbalance {id} {sum}`      | Пополнить баланс пользователя                  |
| `/news {текст}`               | Опубликовать новость (отображается в дашборде) |
| `/notify {id} {текст}`        | Личное сообщение пользователю                  |

---

## Полезные команды

```bash
# Статус сервисов
systemctl status tg-tunnel vpn-bot vpn-api --no-pager

# Рестарт
systemctl restart tg-tunnel vpn-bot vpn-api

# Логи в реальном времени
journalctl -u vpn-bot -f
journalctl -u vpn-api -f

# Проверить что порты слушают
ss -tlnp | grep -E '443|4443|4446|8080|8388|8443'

# Проверить подписку (как видит клиент)
curl -s -A "HappProxy/1.0" "https://your-domain.com/YOUR_KEY" | base64 -d

# Проверить туннель
curl --socks5 127.0.0.1:1080 https://api.telegram.org

# Обновить SSL
certbot renew --nginx

# Проверить nginx
nginx -t && systemctl reload nginx

# Отключить SSL в x-ui панели (если сломалась)
sqlite3 /etc/x-ui/x-ui.db "UPDATE settings SET value='' WHERE key='webCertFile';"
sqlite3 /etc/x-ui/x-ui.db "UPDATE settings SET value='' WHERE key='webKeyFile';"
x-ui stop && x-ui start
```

---

## Известные проблемы

| Проблема                                 | Решение                                                              |
|------------------------------------------|----------------------------------------------------------------------|
| Бот не коннектится к Telegram            | `systemctl restart tg-tunnel`                                        |
| `WRONG_VERSION_NUMBER` при add_client    | `XUI_HOST` должен быть `http://`, не `https://`                      |
| x-ui не стартует, порт занят             | `fuser -k 4443/tcp && systemctl restart x-ui`                        |
| 502 Bad Gateway                          | `systemctl start vpn-api`                                            |
| Дублирование email в xray при продлении  | Суффиксы обязательны: `_ws`, `_xhttp`                                |
| CF блокирует мобильный трафик            | CDN Direct серверы используют прямой IP, не CF IP                    |
| `stream` directive unknown в nginx       | `apt install libnginx-mod-stream`                                    |
| Панель x-ui не открывается в браузере    | Chrome/Firefox блокируют нестандартные порты — используй SSH-туннель |
| x-ui панель делает 307 redirect на HTTPS | Сбросить cert в sqlite, см. выше                                     |
| proxychains гонит 127.0.0.1 через socks5 | `localnet 127.0.0.0/255.0.0.0` в proxychains4.conf                   |

---

## Зависимости

```
aiogram>=3.0
fastapi
uvicorn
aiohttp
aiosqlite
```

```bash
pip install -r requirements.txt
```

---

## Лицензия

MIT
