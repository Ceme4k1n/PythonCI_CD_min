from telebot import TeleBot
from telebot.types import Message, CallbackQuery
from config.config import Config
from core.project_manager import ProjectManager
from core.docker_monitor import DockerMonitor
from utils.error_handler import ErrorHandler
from .keyboard import Keyboard
from core.version_manager import VersionManager
from core.test_environment import TestEnvironment
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
        """Регистрация всех обработчиков"""
        # Команды
        self.bot.message_handler(commands=['start'])(self.handle_start)
        self.bot.message_handler(commands=['help'])(self.handle_help)
        
        # Важно: регистрируем обработчик текстовых сообщений
        self.bot.message_handler(content_types=['text'])(self.handle_message)
        
        # Callback запросы - все через handle_callback
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
        
    @ErrorHandler.handle_error
    async def handle_help(self, message: Message):
        """Обработка команды /help"""
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
            # Получаем пользователя для всех callback запросов
            user = await self.project_manager.db.get_user(str(call.from_user.id))
            if not user:
                await self.bot.answer_callback_query(
                    call.id,
                    "Пожалуйста, начните с команды /start"
                )
                return
            
            # Маршрутизация callback запросов
            if call.data == "add_project":
                await self.handle_add_project(call, user)
            elif call.data == "settings":
                await self.handle_settings(call, user)
            elif call.data == "logs":
                await self.handle_logs(call, user)
            elif call.data == "intervals":
                await self.handle_intervals(call, user)
            elif call.data == "deploy":
                await self.handle_deploy(call, user)
            elif call.data == "stats":
                await self.handle_stats(call, user)
            elif call.data.startswith('versions_'):
                await self.handle_versions(call, user)
            elif call.data.startswith('rollback_'):
                await self.handle_rollback(call, user)
            elif call.data.startswith('test_'):
                await self.handle_test_environment(call, user)
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
        try:
            instruction = (
                "📝 Введите данные проекта в формате:\n"
                "name|repo_url|branch\n\n"
                "Например:\n"
                "my_project|https://github.com/user/repo|main"
            )
            
            # Сохраняем состояние - ожидаем ввод данных проекта
            self.waiting_for_project_data = True
            
            await self.bot.edit_message_text(
                instruction,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=self.keyboard.main_menu()
            )
        except Exception as e:
            logger.error(f"Error in handle_add_project: {str(e)}")
            await self.bot.answer_callback_query(
                call.id,
                "❌ Ошибка при добавлении проекта"
            )

    @ErrorHandler.handle_error
    async def handle_message(self, message: Message):
        """Обработка текстовых сообщений"""
        try:
            if hasattr(self, 'waiting_for_project_data') and self.waiting_for_project_data:
                # Парсим данные проекта
                try:
                    name, repo_url, branch = message.text.strip().split('|')
                    
                    # Создаем проект
                    project = await self.project_manager.create_project(
                        user_id=message.from_user.id,
                        name=name.strip(),
                        repo_url=repo_url.strip(),
                        branch=branch.strip()
                    )
                    
                    # Клонируем репозиторий
                    if await self.project_manager.clone_repository(project):
                        await self.bot.reply_to(
                            message,
                            f"✅ Проект {name} успешно добавлен и склонирован",
                            reply_markup=self.keyboard.main_menu()
                        )
                    else:
                        await self.bot.reply_to(
                            message,
                            f"❌ Ошибка при клонировании репозитория {repo_url}"
                        )
                        
                except ValueError:
                    await self.bot.reply_to(
                        message,
                        "❌ Неверный формат. Используйте: name|repo_url|branch"
                    )
                    
                # Сбрасываем состояние
                self.waiting_for_project_data = False
                
        except Exception as e:
            logger.error(f"Error in handle_message: {str(e)}")
            await self.bot.reply_to(
                message,
                "❌ Произошла ошибка при обработке сообщения"
            )
        
    @ErrorHandler.handle_error
    async def handle_stats(self, call: CallbackQuery, user):
        """Обработка запроса статистики"""
        try:
            if not self.docker_monitor:
                await self.bot.edit_message_text(
                    "⚠️ Мониторинг Docker отключен",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=self.keyboard.main_menu()
                )
                return
            
            stats = self.docker_monitor.get_container_stats("cicd_bot")
            if stats:
                stats_text = (
                    "*📋 Статистика системы*\n\n"
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
        except Exception as e:
            logger.error(f"Error in handle_stats: {str(e)}")
            await self.bot.answer_callback_query(
                call.id,
                "❌ Ошибка при получении статистики"
            )
        
    @ErrorHandler.handle_error
    async def handle_versions(self, call: CallbackQuery, user):
        """Обработка запроса версий проекта"""
        try:
            project_id = int(call.data.split('_')[1])
            project = await self.project_manager.get_project(project_id)
            
            version_manager = VersionManager(project.project_path)
            versions = version_manager.get_versions()
            
            if not versions:
                await self.bot.edit_message_text(
                    "❌ Версии не найдены",
                    call.message.chat.id,
                    call.message.message_id
                )
                return
            
            versions_text = "*📋 Доступные версии:*\n\n"
            for version in versions:
                versions_text += (
                    f"*Версия {version.version_number}*\n"
                    f"Дата: {version.commit_date}\n"
                    f"Сообщение: {version.commit_message}\n"
                    f"Хэш: `{version.commit_hash[:8]}`\n\n"
                )
            
            await self.bot.edit_message_text(
                versions_text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown',
                reply_markup=self.keyboard.versions_menu(project_id)
            )
            
        except Exception as e:
            logger.error(f"Error in handle_versions: {str(e)}")
            await self.bot.answer_callback_query(
                call.id,
                "❌ Ошибка при получении версий"
            )

    @ErrorHandler.handle_error
    async def handle_rollback(self, call: CallbackQuery, user):
        """Обработка отката к версии"""
        try:
            _, project_id, version = call.data.split('_')
            project_id = int(project_id)
            version = int(version)
            
            project = await self.project_manager.get_project(project_id)
            version_manager = VersionManager(project.project_path)
            
            success, message = await version_manager.rollback_to_version(version)
            
            if success:
                await self.bot.edit_message_text(
                    f"✅ {message}",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=self.keyboard.main_menu()
                )
            else:
                await self.bot.answer_callback_query(
                    call.id,
                    f"❌ {message}"
                )
            
        except Exception as e:
            logger.error(f"Error in handle_rollback: {str(e)}")
            await self.bot.answer_callback_query(
                call.id,
                "❌ Ошибка при откате версии"
            )

    @ErrorHandler.handle_error
    async def handle_test_environment(self, call: CallbackQuery, user):
        """Обработка запуска тестового окружения"""
        try:
            project_id = int(call.data.split('_')[1])
            project = await self.project_manager.get_project(project_id)
            
            # Получаем тестовые переменные окружения
            test_config = await self.project_manager.get_test_config(project_id)
            
            # Создаем тестовое окружение
            test_env = TestEnvironment(project.project_path, test_config)
            
            # Настраиваем окружение
            success, message = await test_env.setup()
            if not success:
                await self.bot.answer_callback_query(
                    call.id,
                    f"❌ {message}"
                )
                return
            
            # Запускаем тесты
            success, output = await test_env.run_tests()
            
            # Очищаем окружение
            await test_env.cleanup()
            
            # Формируем отчет
            report = (
                "📋 *Результаты тестирования*\n\n"
                f"Проект: {project.name}\n"
                f"Статус: {'✅ Успешно' if success else '❌ Ошибка'}\n\n"
                "```\n"
                f"{output[:1000]}...\n"  # Ограничиваем вывод
                "```"
            )
            
            await self.bot.edit_message_text(
                report,
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown',
                reply_markup=self.keyboard.main_menu()
            )
            
        except Exception as e:
            logger.error(f"Error in handle_test_environment: {str(e)}")
            await self.bot.answer_callback_query(
                call.id,
                "❌ Ошибка при запуске тестового окружения"
            )

    @ErrorHandler.handle_error
    async def handle_confirmation(self, call: CallbackQuery, user):
        """Обработка подтверждений действий"""
        try:
            action, *params = call.data.split('_')[1:]
            
            if action == "add":
                # Логика подтверждения добавления проекта
                await self.bot.edit_message_text(
                    "✅ Проект успешно добавлен",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=self.keyboard.main_menu()
                )
            else:
                await self.bot.answer_callback_query(
                    call.id,
                    "❌ Неизвестное действие"
                )
            
        except Exception as e:
            logger.error(f"Error in handle_confirmation: {str(e)}")
            await self.bot.answer_callback_query(
                call.id,
                "❌ Ошибка при обработке подтверждения"
            )

    @ErrorHandler.handle_error
    async def handle_deploy(self, call: CallbackQuery, user):
        """Обработка запроса на деплой"""
        try:
            projects = await self.project_manager.get_projects(user.id)
            if not projects:
                await self.bot.edit_message_text(
                    "❌ У вас нет добавленных проектов",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=self.keyboard.main_menu()
                )
                return
            
            await self.bot.edit_message_text(
                "📋 Выберите проект для деплоя:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=self.keyboard.project_list(projects)
            )
            
        except Exception as e:
            logger.error(f"Error in handle_deploy: {str(e)}")
            await self.bot.answer_callback_query(
                call.id,
                "❌ Ошибка при обработке деплоя"
            )

    @ErrorHandler.handle_error
    async def handle_settings(self, call: CallbackQuery, user):
        """Обработка меню настроек"""
        try:
            settings_text = (
                "⚙️ *Настройки*\n\n"
                "Выберите раздел настроек:"
            )
            
            await self.bot.edit_message_text(
                settings_text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown',
                reply_markup=self.keyboard.settings_menu()
            )
        except Exception as e:
            logger.error(f"Error in handle_settings: {str(e)}")
            await self.bot.answer_callback_query(
                call.id,
                "❌ Ошибка при открытии настроек"
            )

    @ErrorHandler.handle_error
    async def handle_logs(self, call: CallbackQuery, user):
        """Обработка просмотра логов"""
        try:
            with open('bot.log', 'r') as f:
                logs = f.readlines()[-self.config.max_log_lines:]
                
            log_text = (
                "*📋 Последние логи:*\n\n"
                "```\n"
                f"{''.join(logs)}\n"
                "```"
            )
            
            await self.bot.edit_message_text(
                log_text[:4000],  # Telegram ограничение
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown',
                reply_markup=self.keyboard.settings_menu()
            )
        except Exception as e:
            logger.error(f"Error in handle_logs: {str(e)}")
            await self.bot.answer_callback_query(
                call.id,
                "❌ Ошибка при получении логов"
            )

    @ErrorHandler.handle_error
    async def handle_intervals(self, call: CallbackQuery, user):
        """Обработка настройки интервалов"""
        try:
            intervals_text = (
                "*⚙️ Текущие интервалы:*\n\n"
                f"• Проверка Git: {self.config.default_check_interval} сек\n"
                f"• Таймаут тестов: {self.config.test_timeout} сек\n\n"
                "Для изменения отправьте команду:\n"
                "`/interval git 300`\n"
                "или\n"
                "`/interval test 600`"
            )
            
            await self.bot.edit_message_text(
                intervals_text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown',
                reply_markup=self.keyboard.settings_menu()
            )
        except Exception as e:
            logger.error(f"Error in handle_intervals: {str(e)}")
            await self.bot.answer_callback_query(
                call.id,
                "❌ Ошибка при получении интервалов"
            ) 