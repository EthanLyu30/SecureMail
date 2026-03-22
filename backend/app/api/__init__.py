# API package
from .auth import router as auth_router
from .mail import router as mail_router
from .group import router as group_router

__all__ = ['auth_router', 'mail_router', 'group_router']