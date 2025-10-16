"""
User Management Service Module

This module provides user management functionality for the admin panel.
It includes listing and searching operations for users.
"""

from aiogram import Router

from .listing import listing_router
from .search import search_router

# Create main router for user management
user_management_router = Router()

# Include sub-routers
user_management_router.include_router(listing_router)
user_management_router.include_router(search_router)

__all__ = [
    'user_management_router',
    'listing_router',
    'search_router'
]

