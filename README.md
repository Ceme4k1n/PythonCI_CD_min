# Python CI/CD Telegram Bot

Система непрерывной интеграции и развертывания (CI/CD) с интерфейсом Telegram-бота.

## Текущий статус проекта

Реализован базовый функционал:
- ✅ Основная структура проекта
- ✅ Мониторинг Git репозиториев
- ✅ Управление Docker контейнерами
- ✅ Базовый интерфейс Telegram бота
- ✅ Система обработки ошибок
- ⏳ Система откатов версий (в разработке)
- ⏳ Тестовое окружение (в разработке)

## Структура проекта

```
cicd_bot/
├── config/          # Конфигурация
│   └── config.py    # Настройки приложения
├── core/            # Ядро системы
│   ├── project_manager.py  # Управление проектами
│   ├── git_monitor.py      # Мониторинг Git
│   └── docker_monitor.py   # Мониторинг Docker
├── database/        # Работа с БД
│   └── db_manager.py
├── bot/            # Telegram бот
│   ├── handlers.py  # Обработчики команд
│   └── keyboard.py  # Клавиатура бота
├── utils/          # Утилиты
│   └── error_handler.py
├── main.py         # Точка входа
├── requirements.txt # Зависимости
└── Dockerfile      # Сборка контейнера
```

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/cicd-bot.git
cd cicd-bot
```

2. Создайте файл .env:
```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_CHAT_ID=your_admin_chat_id
PROJECTS_DIR=/projects
DATABASE_PATH=database/cicd.db
```

3. Запустите через Docker:
```bash
docker build -t cicd_bot .
docker run -d --name cicd_bot \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /path/to/projects:/projects \
    --env-file .env \
    cicd_bot
```

## Использование

1. Запустите бота в Telegram: /start
2. Используйте меню для:
   - Добавления проектов
   - Настройки переменных окружения
   - Запуска проектов
   - Просмотра статистики

## Требования

- Python 3.9+
- Docker
- Git

## Лицензия

GNU General Public License v3.0

## Контакты

- Email: gorelyj@gmail.com
- Telegram: [@PlcAutomationsBolid](https://t.me/PlcAutomationsBolid)
- GitHub: [goreliy](https://github.com/goreliy)
