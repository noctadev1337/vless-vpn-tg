from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command  # Добавь в начало к остальным импортам
from bot.utils import try_delete

from bot.instance import router
from bot.keyboards import kb_instr, kb_instr_back
from bot.texts import INSTR
from bot.utils import send


@router.callback_query(F.data == "instr")
async def cb_instr(call: CallbackQuery):
    await call.answer()
    await send(
        call.from_user.id,
        "📖 <b>Инструкции по подключению</b>\n\nВыбери свою платформу 👇",
        kb_instr(),
    )


@router.callback_query(F.data.startswith("instr_"))
async def cb_instr_platform(call: CallbackQuery):
    await call.answer()
    platform = call.data[6:]
    text = INSTR.get(platform, "❌ Инструкция не найдена")
    await send(call.from_user.id, text, kb_instr_back())


@router.message(Command("instructions"))
async def cmd_instructions(msg: Message):
    await try_delete(msg)
    await send(
        msg.from_user.id,
        "📖 <b>Инструкции по подключению</b>\n\nВыбери свою платформу 👇",
        kb_instr(),  # Используем твою существующую клавиатуру
    )
