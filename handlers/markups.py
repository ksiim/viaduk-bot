from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from bot import bot

from .callbacks import *

table_path = 'tables/garages.xlsx'


async def generate_start_text(message):
    return f"Привет, {message.from_user.full_name}! Я - бот"