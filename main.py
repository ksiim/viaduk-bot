from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

from bot import dp, bot

import logging

import handlers

from models.databases import create_database


logging.basicConfig(level=logging.INFO)

async def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(handlers.update_debts, trigger="cron", day=1)
    scheduler.start()

async def main():
    await start_scheduler()
    await create_database()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())