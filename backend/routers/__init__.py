# routers/__init__.py
from .login import router as login_router
from .auth import router as auth_router
from .admin import router as admin_router
from .room import router as rooms_router

__all__ = ["login_router", "auth_router", "admin_router", "rooms_router"]