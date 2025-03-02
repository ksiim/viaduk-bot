import io
import aiofiles
from aiogram import F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, CallbackQuery, FSInputFile
)
from sqlalchemy import select, update
from models.databases import Session
from bot import dp, bot

from models.dbs.orm import Orm
from models.dbs.models import *
from utils.table_parser import Parser

from .callbacks import *
from .markups import *
from .states import *

async def update_debts():
    parser = Parser(table_path)
    await parser.update_debts()

@dp.message(Command('start'))
async def start_message_handler(message: Message, state: FSMContext):
    await state.clear()
    
    await Orm.create_user(message)
    await send_start_message(message)
    
async def send_start_message(message: Message):
    await bot.send_message(
        chat_id=message.from_user.id,
        text=await generate_start_text(message),
    )
    
@dp.message(Command('update'))
async def update_message_handler(message: Message):
    parser = Parser(table_path)
    await parser.update_debts()
    await message.answer("Таблица успешно обновлена")
    
@dp.message(Command('debt'))
async def debt_message_handler(message: Message, state: FSMContext):
    await state.clear()
    
    try:
        garage_number = message.text.split(' ')[1]
        garage_number = int(garage_number)
    except ValueError:
        return await message.answer("Номер гаража должен быть числом")
    
    parser = Parser(table_path)
    debt = await parser.get_debt(garage_number)
    payment = await parser.get_payment(garage_number)
    text = await generate_debt_text(debt, payment)
    
    await message.reply(
        text=text,
    )
    
async def generate_debt_text(debt: str, payment: str):
    text = f"Взнос за гараж {payment}₽\n"
    if debt is None:
        return "Гараж не найден"
    elif debt < 0:
        text += f"Долг по гаражу составляет {int(debt) * -1}₽"
    else:
        text += f"Переплата по гаражу составляет {debt}₽"
    return text


@dp.message(Command('doadmin'))
async def doadmin_message_handler(message: Message):
    
    try: 
        user_id = message.text.split(' ')[1]
        user_id = int(user_id)
    except ValueError:
        return await message.answer("ID пользователя должен быть числом")
    
    async with Session() as session:
        query = (
            select(User)
            .where(User.telegram_id == user_id)
        )
        user = (await session.execute(query)).scalar_one_or_none()
    
        if user is None:
            return await message.answer("Пользователь не найден")
        
        user.is_admin = not user.is_admin
        await session.merge(user)
        await session.commit()
        await session.refresh(user)
        
        await message.answer("Пользователь успешно обновлен (он стал админом)" if user.is_admin else "Пользователь успешно обновлен (он перестал быть админом)")
        
@dp.message(Command('id'))
async def id_message_handler(message: Message):
    await message.answer(f"<code>{message.from_user.id}</code>", parse_mode='HTML')
    
    
@dp.message(F.document)
async def rewrite_table(message: Message):
    if not (await Orm.get_user_by_telegram_id(message.from_user.id)).is_admin:
        return
    
    await download_document(message)
    await message.answer("Таблица успешно обновлена")
    
    
async def download_document(message: Message):
    document = await bot.get_file(message.document.file_id)
    document = await bot.download_file(document.file_path)
    return await write_bytes_IO_to_file(table_path, document)


async def write_bytes_IO_to_file(file_path, bytesIO: io.BytesIO):
    async with aiofiles.open(file_path, 'wb') as file:
        await file.write(bytesIO.read())
    return file_path