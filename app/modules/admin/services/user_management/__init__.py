"""
User Management Service Module

This module provides user management functionality for the admin panel.
It includes listing and searching operations for users.
"""

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from .listing import listing_router
from .search import search_router

# Create main router for user management
user_management_router = Router()

# Include sub-routers
user_management_router.include_router(listing_router)
user_management_router.include_router(search_router)

# Main entry point handler
@user_management_router.message(CommandStart())
async def user_management_start(message: Message):
    """Main entry point for user management service"""
    await message.answer(
        "👥 **User Management Service**\n\n"
        "Available commands:\n"
        "• /users - List all users\n"
        "• /search_users - Search users"
    )

@user_management_router.message(Command("users"))
async def list_users_command(message: Message):
    """Command to list users"""
    # This will be handled by listing module
    pass

@user_management_router.message(Command("search_users"))
async def search_users_command(message: Message):
    """Command to search users"""
    # This will be handled by search module
    pass

__all__ = [
    'user_management_router',
    'listing_router',
    'search_router'
]

