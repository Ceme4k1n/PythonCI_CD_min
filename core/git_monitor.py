import asyncio
import git
from typing import Optional
from datetime import datetime
from database.db_manager import DatabaseManager, Project

class GitMonitor:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.monitoring = False
        
    async def start_monitoring(self):
        self.monitoring = True
        while self.monitoring:
            projects = await self.db.get_all_projects()
            for project in projects:
                await self.check_repository(project)
                await asyncio.sleep(project.check_interval)
                
    async def stop_monitoring(self):
        self.monitoring = False
        
    async def check_repository(self, project: Project) -> Optional[str]:
        try:
            repo = git.Repo(project.project_path)
            repo.remotes.origin.fetch()
            
            current_commit = repo.head.commit.hexsha
            if current_commit != project.last_commit:
                await self.db.update_project_commit(project.id, current_commit)
                return current_commit
            return None
            
        except Exception as e:
            print(f"Error checking repository {project.name}: {str(e)}")
            return None 