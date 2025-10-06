"""
User Listing Module

This module handles listing and displaying users in the admin panel.
"""

from aiogram import Router

# Create router for user listing
listing_router = Router()

# Import handlers
from .handlers import *

__all__ = ['listing_router']

