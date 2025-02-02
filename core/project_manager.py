import os
import git
from typing import Optional, Dict, List
from database.db_manager import DatabaseManager, Project
import logging

logger = logging.getLogger('project_manager')

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

    async def create_project(self, user_id: int, name: str, repo_url: str, branch: str):
        """Создание нового проекта"""
        try:
            logger.info(f"Creating project: {name} for user {user_id}")
            logger.info(f"Projects dir: {self.projects_dir}")
            
            project_path = os.path.join(self.projects_dir, name)
            logger.info(f"Project path will be: {project_path}")
            
            # Создаем запись в БД
            project = await self.db.create_project(
                user_id=user_id,
                name=name,
                repo_url=repo_url,
                project_path=project_path,
                check_interval=300
            )
            
            if project:
                logger.info(f"Project created in DB with ID: {project.id}")
                # Добавляем branch к объекту проекта
                project.branch = branch
                logger.info(f"Added branch {branch} to project")
            else:
                logger.error("Failed to create project in DB")
            
            return project
            
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            return None
            
    async def clone_repository(self, project) -> bool:
        """Клонирование репозитория"""
        try:
            if not project:
                logger.error("Project object is None")
                return False
            
            logger.info(f"Starting clone for project: {project.name}")
            projects_dir = os.path.abspath(self.projects_dir)
            project_path = os.path.join(projects_dir, project.name)
            
            logger.info(f"Full project path: {project_path}")
            logger.info(f"Repository URL: {project.repo_url}")
            
            # Проверяем и создаем директорию
            if os.path.exists(project_path):
                logger.info(f"Removing existing directory: {project_path}")
                import shutil
                shutil.rmtree(project_path)
            
            logger.info(f"Creating directory: {projects_dir}")
            os.makedirs(projects_dir, exist_ok=True)
            
            # Проверяем права доступа
            logger.info(f"Checking permissions for {projects_dir}")
            try:
                test_file = os.path.join(projects_dir, 'test.txt')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                logger.info("Write permissions OK")
            except Exception as e:
                logger.error(f"Permission test failed: {str(e)}")
                return False
            
            # Пробуем клонировать с полными путями
            try:
                logger.info(f"Cloning {project.repo_url} to {project_path}")
                repo = git.Repo.clone_from(
                    project.repo_url,
                    project_path,
                    branch=project.branch
                )
                logger.info("Repository cloned successfully")
                return True
            
            except git.exc.GitCommandError as e:
                logger.error(f"Git command error: {str(e)}")
                return False
            
        except Exception as e:
            logger.error(f"Error cloning repository: {str(e)}")
            logger.exception(e)  # Полный стек ошибки
            return False 