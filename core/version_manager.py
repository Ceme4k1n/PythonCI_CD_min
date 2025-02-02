import os
import git
from typing import List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger('version_manager')

@dataclass
class Version:
    commit_hash: str
    commit_message: str
    commit_date: str
    version_number: int

class VersionManager:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.repo = None
        try:
            self.repo = git.Repo(project_path)
        except git.exc.InvalidGitRepositoryError:
            logger.error(f"Invalid git repository: {project_path}")

    def get_versions(self, limit: int = 10) -> List[Version]:
        """Получение списка версий"""
        versions = []
        try:
            for i, commit in enumerate(self.repo.iter_commits('master', max_count=limit)):
                versions.append(Version(
                    commit_hash=commit.hexsha,
                    commit_message=commit.message.strip(),
                    commit_date=commit.committed_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                    version_number=i + 1
                ))
            return versions
        except Exception as e:
            logger.error(f"Error getting versions: {str(e)}")
            return []

    async def rollback_to_version(self, version_number: int) -> Tuple[bool, str]:
        """Откат к определенной версии"""
        try:
            versions = self.get_versions(limit=version_number)
            if not versions or len(versions) < version_number:
                return False, "Версия не найдена"

            target_version = versions[version_number - 1]
            
            # Очистка рабочей директории
            self.repo.git.reset('--hard')
            self.repo.git.clean('-fd')
            
            # Переключение на нужный коммит
            self.repo.git.checkout(target_version.commit_hash)
            
            return True, f"Успешный откат к версии {version_number}"
            
        except Exception as e:
            error_msg = f"Ошибка при откате: {str(e)}"
            logger.error(error_msg)
            return False, error_msg 