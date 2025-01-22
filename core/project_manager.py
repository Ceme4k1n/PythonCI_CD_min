import os
import git
from typing import Optional, Dict, List
from database.db_manager import DatabaseManager, Project

class ProjectManager:
    def __init__(self, db_manager: DatabaseManager, projects_dir: str):
        self.db = db_manager
        self.projects_dir = projects_dir
        
    async def add_project(self, name: str, repo_url: str, project_path: str, check_interval: int) -> Project:
        # Проверяем существование директории
        full_path = os.path.join(self.projects_dir, project_path)
        os.makedirs(full_path, exist_ok=True)
        
        # Добавляем проект в базу данных
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO projects (name, repo_url, project_path, check_interval)
                VALUES (?, ?, ?, ?)
            ''', (name, repo_url, project_path, check_interval))
            project_id = cursor.lastrowid
            
        return Project(
            id=project_id,
            name=name,
            repo_url=repo_url,
            project_path=project_path,
            check_interval=check_interval
        )
        
    async def deploy_project(self, project: Project, is_test: bool = False) -> bool:
        try:
            # Получаем конфигурационные переменные
            env_vars = self._get_project_config(project.id, is_test)
            
            # Клонируем или обновляем репозиторий
            repo_path = os.path.join(self.projects_dir, project.project_path)
            if not os.path.exists(os.path.join(repo_path, '.git')):
                git.Repo.clone_from(project.repo_url, repo_path)
            else:
                repo = git.Repo(repo_path)
                repo.remotes.origin.pull()
                
            # Создаем виртуальное окружение
            self._setup_venv(repo_path)
            
            # Запускаем проект
            self._run_project(repo_path, env_vars)
            
            return True
            
        except Exception as e:
            # Логируем ошибку
            print(f"Error deploying project {project.name}: {str(e)}")
            return False
            
    def _setup_venv(self, project_path: str):
        # Создаем виртуальное окружение
        os.system(f'python -m venv {os.path.join(project_path, "venv")}')
        
        # Устанавливаем зависимости
        requirements_path = os.path.join(project_path, 'requirements.txt')
        if os.path.exists(requirements_path):
            os.system(f'{os.path.join(project_path, "venv/bin/pip")} install -r {requirements_path}') 