import asyncio
import logging
import sys
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

API_TOKEN = "token from @Botfather"
ADMIN_USER_ID = id #id admins

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

last_request_time = {}
lock = asyncio.Lock()

class UserStates(StatesGroup):
    waiting_for_text = State()

@router.message(Command("start"))
async def send_welcome(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    async with lock:
        now = datetime.now()
        last_time = last_request_time.get(user_id)

        if last_time and now - last_time < timedelta(minutes=50):
            remaining_time = timedelta(minutes=50) - (now - last_time)
            await message.reply(f"Пожалуйста, подождите еще {int(remaining_time.total_seconds() // 60)} минут и {int(remaining_time.total_seconds() % 60)} секунд перед следующим запросом.")
            return

    await state.set_state(UserStates.waiting_for_text)
    await message.reply("Пожалуйста, введите текст вашего сообщения:")

@router.message(UserStates.waiting_for_text)
async def process_text(message: Message, state: FSMContext):
    await state.update_data(user_text=message.text)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить отправку", callback_data="confirm_send"),
                InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_send")
            ]
        ]
    )
    
    await message.reply(
        f"Ваш текст:\n\n{message.text}\n\nПодтвердите отправку или отмените:",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "confirm_send")
async def confirm_send(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    user_text = user_data.get("user_text", "")
    
    async with lock:
        last_request_time[callback.from_user.id] = datetime.now()
    
    admin_message = (
        f"<b>Новый запрос от пользователя:</b>\n\n"
        f"ЮЗ: @{callback.from_user.username} | ID: <code>{callback.from_user.id}</code>\n"
        f"<b>Имя пользователя:</b> {callback.from_user.full_name}\n"
        f"\n<b>Текст сообщения:</b>\n{user_text}"
    )
    
    await bot.send_message(ADMIN_USER_ID, admin_message, parse_mode='HTML')
    await callback.message.edit_text("Ваше сообщение отправлено администратору. Скоро он с вами свяжется.\nСделано студиями: @exfa_studio &  @coxerhub & @ayalastudio")
    await state.clear()

@router.callback_query(F.data == "cancel_send")
async def cancel_send(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Отправка отменена.")
    await state.clear()

dp.include_router(router)

async def main() -> None:
    bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())