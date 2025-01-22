from telebot import TeleBot
from telebot.types import Message, CallbackQuery
from config.config import Config
from core.project_manager import ProjectManager
from core.docker_monitor import DockerMonitor
from utils.error_handler import ErrorHandler
from .keyboard import Keyboard
import logging

logger = logging.getLogger('handlers')

class BotHandlers:
    def __init__(
        self,
        bot: TeleBot,
        config: Config,
        project_manager: ProjectManager,
        docker_monitor: DockerMonitor,
        error_handler: ErrorHandler
    ):
        self.bot = bot
        self.config = config
        self.project_manager = project_manager
        self.docker_monitor = docker_monitor
        self.error_handler = error_handler
        self.keyboard = Keyboard()
        
        self.register_handlers()
        
    def register_handlers(self):
        # Команды
        self.bot.message_handler(commands=['start'])(self.handle_start)
        self.bot.message_handler(commands=['help'])(self.handle_help)
        
        # Callback запросы
        self.bot.callback_query_handler(func=lambda call: True)(self.handle_callback)
        
    @ErrorHandler.handle_error
    async def handle_start(self, message: Message):
        """Обработка команды /start"""
        try:
            # Получаем или создаем пользователя
            user = await self.project_manager.db.get_user(str(message.from_user.id))
            if not user:
                user = await self.project_manager.db.create_user(
                    str(message.from_user.id),
                    message.from_user.username or "unknown"
                )
                
            welcome_text = (
                f"👋 Добро пожаловать, {user.username}!\n\n"
                "🤖 Я - бот для управления CI/CD процессами.\n\n"
                "Что я умею:\n"
                "• Добавлять и управлять проектами\n"
                "• Автоматически отслеживать изменения в Git\n"
                "• Разворачивать проекты в Docker\n"
                "• Показывать статистику и логи\n\n"
                "Выберите действие в меню ниже:"
            )
            
            await self.bot.send_message(
                message.chat.id,
                welcome_text,
                reply_markup=self.keyboard.main_menu()
            )
        except Exception as e:
            logger.error(f"Error in handle_start: {str(e)}")
            await self.bot.send_message(
                message.chat.id,
                "❌ Произошла ошибка при запуске бота. Попробуйте позже."
            )
        
    @staticmethod
    @ErrorHandler.handle_error
    async def handle_help(self, message: Message):
        help_text = """
*CI/CD Bot - Справка*

Основные команды:
/start - Начать работу
/help - Показать эту справку

Возможности:
• Добавление и управление проектами
• Настройка автоматического деплоя
• Мониторинг состояния проектов
• Откат к предыдущим версиям
• Просмотр статистики Docker

Для начала работы нажмите /start
        """
        await self.bot.send_message(
            message.chat.id,
            help_text,
            parse_mode='Markdown'
        )
        
    @ErrorHandler.handle_error
    async def handle_callback(self, call: CallbackQuery):
        """Обработка callback запросов"""
        try:
            user = await self.project_manager.db.get_user(str(call.from_user.id))
            if not user:
                await self.bot.answer_callback_query(
                    call.id,
                    "Пожалуйста, начните с команды /start"
                )
                return
            
            if call.data == "add_project":
                await self.handle_add_project(call, user)
            elif call.data == "settings":
                await self.bot.edit_message_text(
                    "⚙️ Настройки:",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=self.keyboard.settings_menu()
                )
            elif call.data == "deploy":
                await self.handle_deploy(call, user)
            elif call.data == "stats":
                await self.handle_stats(call, user)
            elif call.data == "help":
                await self.handle_help(call.message)
            elif call.data == "back_to_main":
                await self.bot.edit_message_text(
                    "Главное меню:",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=self.keyboard.main_menu()
                )
            elif call.data.startswith("confirm_"):
                await self.handle_confirmation(call, user)
            
            await self.bot.answer_callback_query(call.id)
            
        except Exception as e:
            logger.error(f"Error in handle_callback: {str(e)}")
            await self.bot.answer_callback_query(
                call.id,
                "❌ Произошла ошибка. Попробуйте позже."
            )
            
    @ErrorHandler.handle_error
    async def handle_add_project(self, call: CallbackQuery, user):
        """Обработка добавления проекта"""
        instruction = (
            "📝 Введите данные проекта в формате:\n"
            "name|repo_url|branch\n\n"
            "Например:\n"
            "my_project|https://github.com/user/repo|main"
        )
        await self.bot.edit_message_text(
            instruction,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=self.keyboard.confirm_menu("add", 0)
        )
        
    @ErrorHandler.handle_error
    async def handle_stats(self, call: CallbackQuery, user):
        """Обработка запроса статистики"""
        stats = self.docker_monitor.get_container_stats("cicd_bot")
        if stats:
            stats_text = (
                "*📊 Статистика системы*\n\n"
                f"CPU: {stats['cpu_percent']}%\n"
                f"RAM: {stats['memory_percent']}%\n"
                f"Использовано: {stats['memory_usage']}\n"
                f"Всего: {stats['memory_limit']}"
            )
        else:
            stats_text = "❌ Не удалось получить статистику"
            
        await self.bot.edit_message_text(
            stats_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=self.keyboard.main_menu()
        ) 