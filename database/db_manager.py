import sqlite3
import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)

@dataclass
class User:
    id: int
    telegram_id: str
    username: str
    is_active: bool = True
    created_at: Optional[str] = None

@dataclass
class Project:
    id: int
    user_id: int  # Связь с пользователем
    name: str
    repo_url: str
    project_path: str
    check_interval: int
    last_commit: Optional[str] = None
    is_running: bool = False
    branch: str = 'main'

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Инициализация базы данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Создаем таблицу пользователей
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id TEXT UNIQUE NOT NULL,
                        username TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Создаем таблицу проектов с привязкой к пользователю
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        repo_url TEXT NOT NULL,
                        project_path TEXT NOT NULL,
                        check_interval INTEGER NOT NULL,
                        last_commit TEXT,
                        is_running BOOLEAN DEFAULT FALSE,
                        branch TEXT DEFAULT 'main',
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        UNIQUE(user_id, name)
                    )
                ''')
                
                # Создаем таблицу конфигурационных переменных
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS project_configs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER,
                        var_name TEXT NOT NULL,
                        var_value TEXT NOT NULL,
                        is_test BOOLEAN DEFAULT FALSE,
                        FOREIGN KEY (project_id) REFERENCES projects (id),
                        UNIQUE(project_id, var_name, is_test)
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise

    async def get_user(self, telegram_id: str) -> Optional[User]:
        """Получение пользователя по telegram_id"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
                row = cursor.fetchone()
                
                if row:
                    return User(
                        id=row[0],
                        telegram_id=row[1],
                        username=row[2],
                        is_active=bool(row[3]),
                        created_at=row[4]
                    )
                return None
                
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return None

    async def create_user(self, telegram_id: str, username: str) -> Optional[User]:
        """Создание нового пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO users (telegram_id, username) VALUES (?, ?)',
                    (telegram_id, username)
                )
                user_id = cursor.lastrowid
                conn.commit()
                
                # Получаем созданного пользователя со всеми полями
                return await self.get_user(telegram_id)
                
        except sqlite3.IntegrityError:
            logger.warning(f"User {telegram_id} already exists")
            return await self.get_user(telegram_id)
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return None

    async def create_project(self, user_id: int, name: str, repo_url: str, project_path: str, check_interval: int) -> Optional[Project]:
        """Создание нового проекта"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO projects 
                    (user_id, name, repo_url, project_path, check_interval)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, name, repo_url, project_path, check_interval))
                
                project_id = cursor.lastrowid
                conn.commit()
                
                return Project(
                    id=project_id,
                    user_id=user_id,
                    name=name,
                    repo_url=repo_url,
                    project_path=project_path,
                    check_interval=check_interval
                )
                
        except sqlite3.IntegrityError as e:
            logger.error(f"Project already exists: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error creating project in DB: {str(e)}")
            return None

    async def get_projects(self, user_id: int) -> List[Project]:
        """Получение списка проектов пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, user_id, name, repo_url, project_path, 
                           check_interval, last_commit, is_running, branch
                    FROM projects 
                    WHERE user_id = ?
                ''', (user_id,))
                
                projects = []
                for row in cursor.fetchall():
                    projects.append(Project(
                        id=row[0],
                        user_id=row[1],
                        name=row[2],
                        repo_url=row[3],
                        project_path=row[4],
                        check_interval=row[5],
                        last_commit=row[6],
                        is_running=bool(row[7]),
                        branch=row[8]
                    ))
                return projects
                
        except Exception as e:
            logger.error(f"Error getting projects: {str(e)}")
            return [] 