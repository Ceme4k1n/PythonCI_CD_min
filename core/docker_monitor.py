import docker
import psutil
from typing import Dict, Optional
import logging

logger = logging.getLogger('docker_monitor')

class DockerMonitor:
    def __init__(self):
        self.client = None
        try:
            self.client = docker.from_env()
        except Exception as e:
            logger.warning(f"Failed to initialize Docker client: {str(e)}")

    def get_container_stats(self, container_name: str) -> Optional[Dict]:
        try:
            if self.client:
                # Пробуем получить статистику через Docker API
                container = self.client.containers.get(container_name)
                stats = container.stats(stream=False)
                
                cpu_stats = stats['cpu_stats']
                memory_stats = stats['memory_stats']
                
                cpu_usage = cpu_stats['cpu_usage']['total_usage']
                system_cpu_usage = cpu_stats['system_cpu_usage']
                cpu_percent = (cpu_usage / system_cpu_usage) * 100
                
                memory_usage = memory_stats['usage']
                memory_limit = memory_stats['limit']
                memory_percent = (memory_usage / memory_limit) * 100
            else:
                # Если Docker API недоступен, используем psutil
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                memory_usage = memory.used
                memory_limit = memory.total

            return {
                'cpu_percent': round(cpu_percent, 2),
                'memory_percent': round(memory_percent, 2),
                'memory_usage': f"{memory_usage / (1024*1024):.2f}MB",
                'memory_limit': f"{memory_limit / (1024*1024):.2f}MB"
            }
            
        except Exception as e:
            logger.error(f"Error getting container stats: {str(e)}")
            return None
            
    def restart_container(self, container_name: str) -> bool:
        try:
            if not self.client:
                logger.error("Docker client not initialized")
                return False
                
            container = self.client.containers.get(container_name)
            container.restart()
            return True
        except Exception as e:
            logger.error(f"Error restarting container: {str(e)}")
            return False 