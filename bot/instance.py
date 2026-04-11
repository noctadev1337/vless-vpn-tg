from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# хранит message_id последнего отправленного сообщения с баннером для каждого чата
_last: dict[int, list[int]] = {}
