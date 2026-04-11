import random
import string
from datetime import datetime, timedelta

import aiosqlite

from shared.config import DB_PATH, PLANS


def _gen_key() -> str:
    def s():
        return "".join(random.choices(string.ascii_letters + string.digits, k=4))

    return f"{s()}-{s()}-{s()}"


async def db_init():
    """Инициализация базы данных + безопасные миграции"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Основные таблицы
        await db.execute("""
                         CREATE TABLE IF NOT EXISTS users
                         (
                             tg_id
                             INTEGER
                             PRIMARY
                             KEY,
                             username
                             TEXT,
                             first_name
                             TEXT,
                             agreed
                             INTEGER
                             DEFAULT
                             0,
                             balance
                             INTEGER
                             DEFAULT
                             0,
                             created_at
                             TEXT
                             DEFAULT (
                             datetime
                         (
                             'now'
                         ))
                             )
                         """)
        await db.execute("""
                         CREATE TABLE IF NOT EXISTS subs
                         (
                             id
                             INTEGER
                             PRIMARY
                             KEY
                             AUTOINCREMENT,
                             tg_id
                             INTEGER
                             NOT
                             NULL,
                             plan
                             TEXT
                             NOT
                             NULL,
                             key
                             TEXT
                             UNIQUE
                             NOT
                             NULL,
                             xui_uuid
                             TEXT
                             NOT
                             NULL,
                             xui_uuid2
                             TEXT,
                             xui_email
                             TEXT
                             NOT
                             NULL,
                             traffic_b
                             INTEGER
                             DEFAULT
                             0,
                             devices
                             INTEGER
                             DEFAULT
                             3,
                             expires_at
                             TEXT
                             NOT
                             NULL,
                             active
                             INTEGER
                             DEFAULT
                             1,
                             notified
                             INTEGER
                             DEFAULT
                             0,
                             created_at
                             TEXT
                             DEFAULT (
                             datetime
                         (
                             'now'
                         ))
                             )
                         """)
        await db.execute("""
                         CREATE TABLE IF NOT EXISTS news
                         (
                             id
                             INTEGER
                             PRIMARY
                             KEY
                             AUTOINCREMENT,
                             text
                             TEXT
                             NOT
                             NULL,
                             created_at
                             TEXT
                             DEFAULT (
                             datetime
                         (
                             'now'
                         ))
                             )
                         """)
        await db.execute("""
                         CREATE TABLE IF NOT EXISTS payments
                         (
                             payment_id
                             TEXT
                             PRIMARY
                             KEY,
                             tg_id
                             INTEGER
                             NOT
                             NULL,
                             plan_id
                             TEXT
                             NOT
                             NULL,
                             status
                             TEXT
                             DEFAULT
                             'pending',
                             created_at
                             TEXT
                             DEFAULT (
                             datetime
                         (
                             'now'
                         ))
                             )
                         """)
        await db.execute("""
                         CREATE TABLE IF NOT EXISTS topups
                         (
                             payment_id
                             TEXT
                             PRIMARY
                             KEY,
                             tg_id
                             INTEGER
                             NOT
                             NULL,
                             amount
                             INTEGER
                             NOT
                             NULL,
                             status
                             TEXT
                             DEFAULT
                             'pending',
                             created_at
                             TEXT
                             DEFAULT (
                             datetime
                         (
                             'now'
                         ))
                             )
                         """)

        # Миграции (добавляем колонки, если их ещё нет)
        migrations = [
            ("users", "balance", "INTEGER DEFAULT 0"),
            ("subs", "xui_uuid2", "TEXT"),
            ("subs", "notified", "INTEGER DEFAULT 0"),
        ]
        for table, col, defn in migrations:
            try:
                await db.execute(f"ALTER TABLE {table} ADD COLUMN {col} {defn}")
            except Exception:
                pass  # колонка уже существует

        await db.commit()


# ====================== USERS ======================

async def db_get_user(tg_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,)) as c:
            return await c.fetchone()


async def db_ensure_user(tg_id, username, first_name):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (tg_id, username, first_name) VALUES (?,?,?)",
            (tg_id, username, first_name or str(tg_id))
        )
        await db.commit()


async def db_agree(tg_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET agreed=1 WHERE tg_id=?", (tg_id,))
        await db.commit()


# ====================== BALANCE ======================

async def db_get_balance(tg_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance FROM users WHERE tg_id=?", (tg_id,)) as c:
            row = await c.fetchone()
            return row[0] if row else 0


async def db_add_balance(tg_id: int, amount: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE tg_id=?",
            (amount, tg_id)
        )
        await db.commit()
        async with db.execute("SELECT balance FROM users WHERE tg_id=?", (tg_id,)) as c:
            row = await c.fetchone()
            return row[0] if row else 0


async def db_deduct_balance(tg_id: int, amount: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance FROM users WHERE tg_id=?", (tg_id,)) as c:
            row = await c.fetchone()
        if not row or row[0] < amount:
            return False

        await db.execute(
            "UPDATE users SET balance = balance - ? WHERE tg_id=? AND balance >= ?",
            (amount, tg_id, amount)
        )
        await db.commit()
        return True


# ====================== TOPUPS ======================

async def db_create_topup(payment_id: str, tg_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO topups (payment_id, tg_id, amount) VALUES (?,?,?)",
            (payment_id, tg_id, amount)
        )
        await db.commit()


async def db_get_topup(payment_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM topups WHERE payment_id=?", (payment_id,)) as c:
            return await c.fetchone()


async def db_mark_topup_done(payment_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE topups SET status='done' WHERE payment_id=?", (payment_id,))
        await db.commit()


# ====================== SUBSCRIPTIONS ======================

async def db_get_sub(tg_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
                """SELECT *
                   FROM subs
                   WHERE tg_id = ?
                     AND active = 1
                     AND expires_at > datetime('now')
                   ORDER BY created_at DESC LIMIT 1""",
                (tg_id,)
        ) as c:
            return await c.fetchone()


async def db_create_sub(tg_id, plan, xui_uuid, xui_email, days, xui_uuid2=None):
    async with aiosqlite.connect(DB_PATH) as db:
        key = _gen_key()
        # Защита от коллизий ключей
        for _ in range(10):
            async with db.execute("SELECT id FROM subs WHERE key=?", (key,)) as c:
                if not await c.fetchone():
                    break
            key = _gen_key()

        p = PLANS[plan]
        traffic_b = p["traffic_gb"] * 1024 ** 3 if p["traffic_gb"] > 0 else 0
        devices = p["devices"]
        expires = datetime.now() + timedelta(days=days)

        await db.execute(
            """INSERT INTO subs
               (tg_id, plan, key, xui_uuid, xui_uuid2, xui_email, traffic_b, devices, expires_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (tg_id, plan, key, xui_uuid, xui_uuid2, xui_email, traffic_b, devices, expires.isoformat())
        )
        await db.commit()
        return key, expires


async def db_extend_sub(tg_id: int, plan_id: str, new_expires: datetime) -> tuple[str, datetime]:
    p = PLANS[plan_id]
    traffic_b = p["traffic_gb"] * 1024 ** 3 if p["traffic_gb"] > 0 else 0
    devices = p["devices"]

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE subs
               SET expires_at=?,
                   plan=?,
                   traffic_b=?,
                   devices=?,
                   notified=0
               WHERE tg_id = ?
                 AND active = 1""",
            (new_expires.isoformat(), plan_id, traffic_b, devices, tg_id)
        )
        await db.commit()

        async with db.execute(
                "SELECT key FROM subs WHERE tg_id=? AND active=1 ORDER BY created_at DESC LIMIT 1",
                (tg_id,)
        ) as c:
            row = await c.fetchone()
            key = row[0] if row else ""
    return key, new_expires


async def db_deactivate(tg_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE subs SET active=0 WHERE tg_id=? AND active=1", (tg_id,))
        await db.commit()


async def db_remove_sub(tg_id: int):
    """Полностью удаляет все подписки пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM subs WHERE tg_id = ?", (tg_id,))
        await db.commit()


async def db_list_subs():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
                """SELECT s.*, u.username, u.first_name
                   FROM subs s
                            JOIN users u ON s.tg_id = u.tg_id
                   WHERE s.active = 1
                     AND s.expires_at > datetime('now')
                   ORDER BY s.expires_at DESC"""
        ) as c:
            return await c.fetchall()


# ====================== NEWS & NOTIFICATIONS ======================

async def db_add_news(text: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO news (text) VALUES (?)", (text,))
        await db.commit()


async def db_get_news(limit: int = 3):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
                "SELECT * FROM news ORDER BY created_at DESC LIMIT ?", (limit,)
        ) as c:
            rows = await c.fetchall()
    return list(reversed(rows))


async def db_has_used_trial(tg_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
                "SELECT id FROM subs WHERE tg_id=? AND plan='trial' LIMIT 1", (tg_id,)
        ) as c:
            return await c.fetchone() is not None


async def db_get_expired():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
                "SELECT * FROM subs WHERE active=1 AND expires_at <= datetime('now')"
        ) as c:
            return await c.fetchall()


async def db_get_subs_for_notify(hours: int, bit: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
                """SELECT *
                   FROM subs
                   WHERE active = 1
                     AND expires_at > datetime('now')
                     AND expires_at <= datetime('now', ?)
                     AND (notified & ?) = 0""",
                (f"+{hours} hours", bit)
        ) as c:
            return await c.fetchall()


async def db_set_notified(sub_id: int, notified: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE subs SET notified=? WHERE id=?", (notified, sub_id))
        await db.commit()
