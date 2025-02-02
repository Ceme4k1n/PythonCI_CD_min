import os
import docker
import logging
from typing import Optional, Dict, Tuple
import asyncio

logger = logging.getLogger('test_environment')

class TestEnvironment:
    def __init__(self, project_path: str, config: Dict):
        self.project_path = project_path
        self.config = config
        self.client = docker.from_env()
        self.container = None
        
    async def setup(self) -> Tuple[bool, str]:
        """Настройка тестового окружения"""
        try:
            # Создаем тестовый контейнер
            self.container = self.client.containers.run(
                'python:3.9-slim',
                command='tail -f /dev/null',  # Держим контейнер запущенным
                detach=True,
                volumes={
                    self.project_path: {
                        'bind': '/app',
                        'mode': 'rw'
                    }
                },
                environment=self.config,
                name=f"test_{os.path.basename(self.project_path)}",
                remove=True
            )
            
            # Устанавливаем зависимости
            exit_code, output = self.container.exec_run(
                "pip install -r /app/requirements.txt"
            )
            
            if exit_code != 0:
                raise Exception(f"Failed to install dependencies: {output.decode()}")
                
            return True, "Тестовое окружение настроено"
            
        except Exception as e:
            error_msg = f"Ошибка настройки тестового окружения: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
            
    async def run_tests(self) -> Tuple[bool, str]:
        """Запуск тестов"""
        try:
            if not self.container:
                return False, "Тестовое окружение не настроено"
                
            # Запускаем тесты
            exit_code, output = self.container.exec_run(
                "python -m pytest /app/tests"
            )
            
            return exit_code == 0, output.decode()
            
        except Exception as e:
            error_msg = f"Ошибка при запуске тестов: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
            
    async def cleanup(self):
        """Очистка тестового окружения"""
        try:
            if self.container:
                self.container.stop()
                self.container.remove()
        except Exception as e:
            logger.error(f"Error cleaning up test environment: {str(e)}") 