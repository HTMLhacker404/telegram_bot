import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import TOKEN, ADMIN_IDS
from database import db  # Импортируем db напрямую
from handlers import user_handlers, admin_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

async def main():
    # Синхронизация админов при запуске    
    db.sync_with_config_admins(ADMIN_IDS)
    logging.info(f"Список администраторов: {db.admins}")
    print(f"Админы после синхронизации: {db.admins}")

    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logging.info("Бот запущен")
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот завершает работу...")
    except Exception as e:
        logging.error(f"Ошибка: {e}")
    finally:
        await bot.session.close()
        logging.info("Сессия бота закрыта")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Работа бота завершена")
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")