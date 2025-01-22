from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

class Keyboard:
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Создание главного меню"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("➕ Добавить проект", callback_data="add_project"),
            InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
            InlineKeyboardButton("🚀 Деплой", callback_data="deploy"),
            InlineKeyboardButton("📊 Статистика", callback_data="stats"),
            InlineKeyboardButton("❓ Помощь", callback_data="help")
        )
        return keyboard

    @staticmethod
    def project_menu(project_id: int) -> InlineKeyboardMarkup:
        """Меню управления проектом"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🔄 Обновить", callback_data=f"update_{project_id}"),
            InlineKeyboardButton("⏹ Остановить", callback_data=f"stop_{project_id}"),
            InlineKeyboardButton("▶️ Запустить", callback_data=f"start_{project_id}"),
            InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
        )
        return keyboard

    @staticmethod
    def settings_menu() -> InlineKeyboardMarkup:
        """Меню настроек"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🔑 Переменные", callback_data="env_vars"),
            InlineKeyboardButton("⏱ Интервалы", callback_data="intervals"),
            InlineKeyboardButton("📝 Логи", callback_data="logs"),
            InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
        )
        return keyboard

    @staticmethod
    def confirm_menu(action: str, project_id: int) -> InlineKeyboardMarkup:
        """Меню подтверждения действия"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("✅ Да", callback_data=f"confirm_{action}_{project_id}"),
            InlineKeyboardButton("❌ Нет", callback_data=f"cancel_{action}_{project_id}")
        )
        return keyboard

    @staticmethod
    def project_list(projects: list) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardMarkup()
        for project in projects:
            keyboard.row(InlineKeyboardButton(
                project.name, 
                callback_data=f"project_{project.id}"
            ))
        keyboard.row(InlineKeyboardButton("◀️ Назад", callback_data="main_menu"))
        return keyboard 