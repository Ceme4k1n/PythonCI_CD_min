import os
from dataclasses import dataclass
from typing import Optional
import logging
import re
import requests

logger = logging.getLogger('config')

@dataclass
class Config:
    bot_token: str
    projects_base_dir: str
    database_path: str
    docker_socket: str
    github_token: Optional[str]
    log_level: str
    default_check_interval: int
    max_log_lines: int
    test_mode: bool
    test_timeout: int
    http_proxy: Optional[str]
    https_proxy: Optional[str]

    def get(self, key: str, default=None):
        """Получение значения конфигурации по ключу"""
        return getattr(self, key.lower(), default)

    @classmethod
    def from_env(cls) -> 'Config':
        try:
            # Обязательные параметры
            bot_token = os.getenv('BOT_TOKEN')
            if not bot_token:
                raise ValueError("BOT_TOKEN is required")

            # Параметры с значениями по умолчанию
            try:
                default_check_interval = int(os.getenv('DEFAULT_CHECK_INTERVAL', '300').strip())
            except ValueError:
                logger.warning("Invalid DEFAULT_CHECK_INTERVAL, using default 300")
                default_check_interval = 300

            try:
                max_log_lines = int(os.getenv('MAX_LOG_LINES', '30').strip())
            except ValueError:
                logger.warning("Invalid MAX_LOG_LINES, using default 30")
                max_log_lines = 30

            try:
                test_timeout = int(os.getenv('TEST_TIMEOUT', '300').strip())
            except ValueError:
                logger.warning("Invalid TEST_TIMEOUT, using default 300")
                test_timeout = 300

            # Безопасное преобразование строки в boolean
            test_mode = os.getenv('TEST_MODE', 'False').strip().lower() in ['true', '1', 'yes']

            return cls(
                bot_token=bot_token,
                projects_base_dir=os.getenv('PROJECTS_DIR', '/projects'),
                database_path=os.getenv('DATABASE_PATH', '/app/database/cicd.db'),
                docker_socket=os.getenv('DOCKER_SOCKET', '/var/run/docker.sock'),
                github_token=os.getenv('GITHUB_TOKEN'),
                log_level=os.getenv('LOG_LEVEL', 'INFO').upper(),
                default_check_interval=default_check_interval,
                max_log_lines=max_log_lines,
                test_mode=test_mode,
                test_timeout=test_timeout,
                http_proxy=os.getenv('HTTP_PROXY'),
                https_proxy=os.getenv('HTTPS_PROXY')
            )
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            # Возвращаем конфигурацию по умолчанию в случае ошибки
            return cls(
                bot_token=os.getenv('BOT_TOKEN', ''),
                projects_base_dir='/projects',
                database_path='/app/database/cicd.db',
                docker_socket='/var/run/docker.sock',
                github_token=None,
                log_level='INFO',
                default_check_interval=300,
                max_log_lines=30,
                test_mode=False,
                test_timeout=300,
                http_proxy=None,
                https_proxy=None
            )

    def validate(self) -> bool:
        """Проверка валидности конфигурации"""
        if not self.bot_token:
            logger.error("BOT_TOKEN is required")
            return False
            
        # Проверка формата токена
        if not re.match(r'^\d+:[A-Za-z0-9_-]{35}$', self.bot_token):
            logger.error("Invalid BOT_TOKEN format")
            return False
            
        # Проверка валидности токена
        try:
            response = requests.get(f'https://api.telegram.org/bot{self.bot_token}/getMe')
            if not response.json().get('ok'):
                logger.error("Invalid BOT_TOKEN: Telegram API check failed")
                return False
        except Exception as e:
            logger.error(f"Failed to verify BOT_TOKEN: {str(e)}")
            return False
        
        # Проверка существования директорий
        for path in [self.projects_base_dir, os.path.dirname(self.database_path)]:
            if not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                except Exception as e:
                    logger.error(f"Failed to create directory {path}: {str(e)}")
                    return False

        return True 