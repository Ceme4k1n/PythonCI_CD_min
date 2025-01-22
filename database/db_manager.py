import sqlite3
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class User:
    id: int
    telegram_id: str
    username: str
    is_active: bool = True

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

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Создаем таблицу пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id TEXT NOT NULL UNIQUE,
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
            
    async def get_user(self, telegram_id: str) -> Optional[User]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, telegram_id, username, is_active FROM users WHERE telegram_id = ?",
                (telegram_id,)
            )
            row = cursor.fetchone()
            if row:
                return User(*row)
            return None
            
    async def create_user(self, telegram_id: str, username: str) -> User:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (telegram_id, username) VALUES (?, ?)",
                (telegram_id, username)
            )
            user_id = cursor.lastrowid
            conn.commit()
            return User(user_id, telegram_id, username) 