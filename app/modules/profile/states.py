"""
Стани для модуля профілю
"""

from aiogram.fsm.state import State, StatesGroup


class ProfileStates(StatesGroup):
    """Стани для редагування профілю"""

    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_phone = State()
    waiting_for_notifications = State()
    waiting_for_privacy_settings = State()
    waiting_for_theme_settings = State()
    waiting_for_language_settings = State()


class SettingsStates(StatesGroup):
    """Стани для налаштувань"""

    waiting_for_notification_preference = State()
    waiting_for_privacy_preference = State()
    waiting_for_theme_preference = State()
    waiting_for_language_preference = State()
