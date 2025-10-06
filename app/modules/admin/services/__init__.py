"""
Admin Panel Services

This module contains all admin panel services including:
- vehicle_management: Vehicle management operations
- user_management: User management operations
"""

from .vehicle_management import router as vehicle_management_router
from .user_management import user_management_router

__all__ = [
    'vehicle_management_router',
    'user_management_router'
]
