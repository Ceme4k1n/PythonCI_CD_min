import asyncio
import logging
import sys
import time
import os
from telebot.async_telebot import AsyncTeleBot
from config.config import Config
from database.db_manager import DatabaseManager
from core.project_manager import ProjectManager
from core.git_monitor import GitMonitor
from core.docker_monitor import DockerMonitor
from utils.error_handler import ErrorHandler
from bot.handlers import BotHandlers
import telebot

async def setup_logging(config: Config):
    """Настройка логирования"""
    try:
        logging.basicConfig(
            level=getattr(logging, config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('bot.log')
            ]
        )
    except Exception as e:
        print(f"Failed to setup logging: {str(e)}")
        # Настройка базового логирования в случае ошибки
        logging.basicConfig(level=logging.INFO)

async def setup_proxy(config: Config):
    """Настройка прокси"""
    if hasattr(config, 'http_proxy'):
        telebot.apihelper.proxy = {
            'http': config.http_proxy,
            'https': config.https_proxy
        }
        os.environ['HTTP_PROXY'] = config.http_proxy
        os.environ['HTTPS_PROXY'] = config.https_proxy

async def init_components(config: Config):
    """Инициализация компонентов с обработкой ошибок"""
    try:
        # Проверка конфигурации
        if not config.validate():
            raise ValueError("Invalid configuration")

        bot = AsyncTeleBot(config.bot_token)
        db_manager = DatabaseManager(config.database_path)
        project_manager = ProjectManager(db_manager, config.projects_base_dir)
        git_monitor = GitMonitor(db_manager)
        docker_monitor = DockerMonitor()
        error_handler = ErrorHandler(bot)

        return bot, db_manager, project_manager, git_monitor, docker_monitor, error_handler
    except Exception as e:
        logging.error(f"Failed to initialize components: {str(e)}")
        raise

async def main():
    try:
        # Загрузка конфигурации
        config = Config.from_env()
        
        # Настройка логирования
        await setup_logging(config)
        logger = logging.getLogger('main')
        
        # Настройка прокси
        await setup_proxy(config)
        
        # Инициализация компонентов
        components = await init_components(config)
        if not components:
            raise RuntimeError("Failed to initialize components")
            
        bot, db_manager, project_manager, git_monitor, docker_monitor, error_handler = components
        
        # Инициализация обработчиков бота
        handlers = BotHandlers(
            bot,
            config,
            project_manager,
            docker_monitor,
            error_handler
        )
        
        # Запуск мониторинга Git репозиториев
        monitoring_task = asyncio.create_task(git_monitor.start_monitoring())
        
        logger.info("Bot started successfully")
        
        # Запуск бота
        await bot.polling(non_stop=True, timeout=60)
        
    except Exception as e:
        logging.error(f"Critical error: {str(e)}")
        # Пауза перед перезапуском
        await asyncio.sleep(5)
        # Перезапуск main()
        await main()

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            logging.info("Bot stopped by user")
            break
        except Exception as e:
            logging.error(f"Bot crashed: {str(e)}")
            # Пауза перед перезапуском
            time.sleep(5) 