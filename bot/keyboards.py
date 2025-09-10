from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_keyboard():
    "Main menu keyboard"
    keyboard = [
        [KeyboardButton(text="👤 Мой профиль")],
        [KeyboardButton(text="🧭 Подобрать маршрут")],
        [KeyboardButton(text="🏪 Магазин")],
        [KeyboardButton(text="⚙️ Настройки")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_profile_keyboard():
    "Profile menu keyboard"
    keyboard = [
        [KeyboardButton(text="📊 Мои баллы")],
        [KeyboardButton(text="📍 Мои маршруты")],
        [KeyboardButton(text="🛍️ Мои покупки")],
        [KeyboardButton(text="🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_settings_keyboard():
    "Settings menu keyboard"
    keyboard = [
        [KeyboardButton(text="✏️ Изменить интересы")],
        [KeyboardButton(text="📱 Изменить телефон")],
        [KeyboardButton(text="🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_route_settings_keyboard():
    "Route settings keyboard"
    keyboard = [
        [KeyboardButton(text="🔢 Изменить количество объектов")],
        [KeyboardButton(text="🔄 Пересоздать маршрут")],
        [KeyboardButton(text="📍 Отправить местоположение")],
        [KeyboardButton(text="🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_shop_keyboard():
    "Shop menu keyboard"
    keyboard = [
        [KeyboardButton(text="🛒 Все товары")],
        [KeyboardButton(text="🏅 Мои баллы")],
        [KeyboardButton(text="📦 Мои покупки")],
        [KeyboardButton(text="🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_back_keyboard():
    "Back button keyboard"
    keyboard = [[KeyboardButton(text="🔙 Назад")]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_confirmation_keyboard():
    "Confirmation keyboard"
    keyboard = [
        [KeyboardButton(text="✅ Да"), KeyboardButton(text="❌ Нет")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_interests_suggestion_keyboard(interests_list):
    "Keyboard with interest suggestions"
    keyboard = []
    for i in range(0, len(interests_list), 2):
        row = []
        row.append(KeyboardButton(text=interests_list[i]))
        if i + 1 < len(interests_list):
            row.append(KeyboardButton(text=interests_list[i + 1]))
        keyboard.append(row)

    keyboard.append([KeyboardButton(text="✅ Готово")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)