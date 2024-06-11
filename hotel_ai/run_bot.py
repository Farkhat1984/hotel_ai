# run_bot.py
import logging
import os
import sys
import asyncio
from bot.handlers import dp, bot
from hotel_ai.functions.functions import create_excel_file


async def main() -> None:

    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
