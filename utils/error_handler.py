import logging
import traceback
from functools import wraps
from typing import Callable, Optional
from telebot import TeleBot

class ErrorHandler:
    def __init__(self, bot: TeleBot, admin_chat_id: int = None):
        self.bot = bot
        self.admin_chat_id = admin_chat_id
        self.logger = logging.getLogger('cicd_bot')
        
    @staticmethod
    def handle_error(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_msg = f"Error in {func.__name__}:\n{str(e)}\n{traceback.format_exc()}"
                logging.error(error_msg)
                return None
        return wrapper 