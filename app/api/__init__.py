from .auth import router_auth, router_users, router_health
from .task import router_task
from .category import router_categories
from .notifications import router_notifications

from .deps import get_current_user

__all__ = [
    "router_auth",
    "router_users",
    "router_health",
    "router_task",
    "router_categories",
    "router_notifications",
    "get_current_user"
]
