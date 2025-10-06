"""
User Search Module

This module handles searching and filtering users in the admin panel.
"""

from aiogram import Router

# Create router for user search
search_router = Router()

# Import handlers
from .handlers import *

__all__ = ['search_router']

