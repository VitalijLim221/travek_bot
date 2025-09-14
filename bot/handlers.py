# bot/handlers.py
from aiogram import Router, F
from aiogram.types import Message, Location
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import json

from bot.database import (
    save_user, get_user, update_user_interests, update_user_route,
    get_user_route, update_route_step, get_route_step,
    add_visited_object, add_points, get_shop_items
)
from bot.deepseek_integration import get_route_from_deepseek, get_interests_suggestions
from bot.location_utils import is_location_match, format_coordinates, calculate_distance
from bot.keyboards import (
    get_main_keyboard, get_profile_keyboard, get_settings_keyboard,
    get_route_settings_keyboard, get_shop_keyboard, get_back_keyboard,
    get_confirmation_keyboard, get_interests_suggestion_keyboard
)
from bot.config import POINTS_PER_OBJECT, LOCATION_ACCURACY

router = Router()


class UserStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_interests = State()
    waiting_for_route_count = State()
    on_route = State()
    changing_interests = State()
    changing_phone = State()
    viewing_shop = State()


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if user:
        await message.answer("👋 С возвращением! Выберите действие:", reply_markup=get_main_keyboard())
    else:
        await message.answer("👋 Добро пожаловать! Введите ваше имя:")
        await state.set_state(UserStates.waiting_for_name)


@router.message(UserStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите ваш номер телефона:")
    await state.set_state(UserStates.waiting_for_phone)


@router.message(UserStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data.get('name')
    phone = message.text

    save_user(message.from_user.id, name, phone)
    await message.answer(f"Спасибо, {name}! Теперь расскажите о ваших интересах (например: музеи, парки, архитектура):")
    await state.set_state(UserStates.waiting_for_interests)


@router.message(UserStates.waiting_for_interests)
async def process_interests(message: Message, state: FSMContext):
    interests = message.text
    # Get suggestions from DeepSeek
    try:
        suggestions = get_interests_suggestions(interests)
        if suggestions and len(suggestions) > 0:
            await message.answer("Вот уточненные интересы. Выберите подходящие или нажмите 'Готово':",
                                 reply_markup=get_interests_suggestion_keyboard(suggestions))
            await state.update_data(original_interests=interests, interests_suggestions=suggestions)
            await state.set_state(UserStates.changing_interests)
            return
    except:
        pass

    update_user_interests(message.from_user.id, interests)
    await message.answer("✅ Ваши интересы сохранены!", reply_markup=get_main_keyboard())
    await state.clear()


@router.message(UserStates.changing_interests)
async def process_interests_selection(message: Message, state: FSMContext):
    if message.text == "✅ Готово":
        data = await state.get_data()
        selected_interests = data.get('selected_interests', [])
        if selected_interests:
            interests_str = ", ".join(selected_interests)
            update_user_interests(message.from_user.id, interests_str)
            await message.answer(f"✅ Ваши интересы обновлены: {interests_str}", reply_markup=get_main_keyboard())
        else:
            # Use original interests
            original = data.get('original_interests', '')
            update_user_interests(message.from_user.id, original)
            await message.answer(f"✅ Ваши интересы сохранены: {original}", reply_markup=get_main_keyboard())
        await state.clear()
    elif message.text in (await state.get_data()).get('interests_suggestions', []):
        data = await state.get_data()
        selected = data.get('selected_interests', [])
        if message.text not in selected:
            selected.append(message.text)
            await state.update_data(selected_interests=selected)
            await message.answer(f"Добавлено: {message.text}")
    else:
        # Add custom interest
        data = await state.get_data()
        selected = data.get('selected_interests', [])
        if message.text not in selected:
            selected.append(message.text)
            await state.update_data(selected_interests=selected)
            await message.answer(f"Добавлено: {message.text}")


@router.message(F.text == "🧭 Подобрать маршрут")
async def start_route_creation(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if not user or not user[5]:  # interests
        await message.answer("Сначала укажите ваши интересы в настройках!")
        return

    await message.answer("Сколько объектов вы хотите в маршруте? (от 1 до 20)")
    await state.set_state(UserStates.waiting_for_route_count)


@router.message(UserStates.waiting_for_route_count)
async def process_route_count(message: Message, state: FSMContext):
    try:
        count = int(message.text)
        if count < 1 or count > 20:
            await message.answer("Пожалуйста, введите число от 1 до 20")
            return
    except ValueError:
        await message.answer("Пожалуйста, введите целое число")
        return

    await state.update_data(route_count=count)

    user = get_user(message.from_user.id)
    interests = user[5]  # interests column

    await message.answer("🕐 Создаю маршрут, это может занять немного времени...")

    # Generate route using DeepSeek
    route = get_route_from_deepseek(interests, count)

    if route:
        update_user_route(message.from_user.id, route)
        update_route_step(message.from_user.id, 0)

        route_text = "Ваш маршрут:\n\n"
        for i, obj in enumerate(route, 1):
            route_text += f"{i}. {obj['name']}\n   {obj['description']}\n"
            route_text += f"   Координаты: {format_coordinates(obj['latitude'], obj['longitude'])}\n\n"

        await message.answer(route_text, reply_markup=get_route_settings_keyboard())
        await state.set_state(UserStates.on_route)
    else:
        await message.answer("Не удалось создать маршрут. Попробуйте позже.", reply_markup=get_main_keyboard())
        await state.clear()


@router.message(F.location)
async def process_location(message: Message, state: FSMContext):
    "Обработка полученных координат пользователя"
    user_lat = message.location.latitude
    user_lon = message.location.longitude

    # Получаем текущего пользователя и его маршрут
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("Пожалуйста, сначала зарегистрируйтесь с помощью /start")
        return

    route = get_user_route(message.from_user.id)
    step = get_route_step(message.from_user.id)

    # Проверяем, есть ли активный маршрут
    if not route or len(route) == 0:
        await message.answer("У вас нет активного маршрута. Сначала создайте маршрут.",
                             reply_markup=get_main_keyboard())
        await state.clear()
        return

    # Проверяем, не завершен ли маршрут
    if step >= len(route):
        await message.answer("Вы уже завершили этот маршрут! Создайте новый маршрут.",
                             reply_markup=get_main_keyboard())
        await state.clear()
        return

    # Получаем текущий объект маршрута
    current_object = route[step]
    target_lat = current_object['latitude']
    target_lon = current_object['longitude']
    object_name = current_object['name']

    # Показываем пользователю его координаты и координаты цели
    location_info = f"📍 Ваши координаты: {format_coordinates(user_lat, user_lon)}\n"
    location_info += f"🎯 Цель ({object_name}): {format_coordinates(target_lat, target_lon)}\n\n"

    # Проверяем совпадение координат
    if is_location_match(user_lat, user_lon, target_lat, target_lon):
        # Координаты совпадают - засчитываем посещение
        add_visited_object(message.from_user.id, current_object)
        add_points(message.from_user.id, POINTS_PER_OBJECT)

        success_message = f"✅ Поздравляем! Вы достигли объекта: {object_name}\n"
        success_message += f"📍 Точность: в пределах {LOCATION_ACCURACY} метров\n"
        success_message += f"💰 +{POINTS_PER_OBJECT} баллов\n\n"

        # Переходим к следующему объекту
        next_step = step + 1
        update_route_step(message.from_user.id, next_step)

        if next_step < len(route):
            # Есть еще объекты в маршруте
            next_object = route[next_step]
            success_message += f"Следующий объект: {next_object['name']}\n"
            success_message += f"{next_object['description']}\n"
            success_message += f"Координаты: {format_coordinates(next_object['latitude'], next_object['longitude'])}"
            await message.answer(success_message, reply_markup=get_route_settings_keyboard())
        else:
            # Маршрут завершен
            total_points = len(route) * POINTS_PER_OBJECT
            success_message += f"🎉 Поздравляем! Вы завершили весь маршрут!\n"
            success_message += f"Всего получено: {total_points} баллов"
            await message.answer(success_message, reply_markup=get_main_keyboard())
            await state.clear()
    else:
        # Координаты не совпадают
        distance = calculate_distance(user_lat, user_lon, target_lat, target_lon)
        fail_message = location_info
        fail_message += f"❌ Вы еще не достигли объекта {object_name}\n"
        fail_message += f"📏 Расстояние до цели: {distance:.0f} метров\n"
        fail_message += f"🎯 Требуемая точность: {LOCATION_ACCURACY} метров\n\n"
        fail_message += "Попробуйте подойти ближе и отправить местоположение снова."
        await message.answer(fail_message, reply_markup=get_route_settings_keyboard())


@router.message(F.text == "📍 Отправить местоположение")
async def request_location(message: Message):
    """Запрос координат у пользователя"""
    await message.answer(
        "Пожалуйста, отправьте ваше текущее местоположение, нажав на скрепку и выбрав 'Геопозиция' или 'Location'")


@router.message(F.text == "🔢 Изменить количество объектов")
async def change_route_count(message: Message, state: FSMContext):
    await message.answer("Сколько объектов вы хотите в маршруте? (от 1 до 20)")
    await state.set_state(UserStates.waiting_for_route_count)


@router.message(F.text == "🔄 Пересоздать маршрут")
async def recreate_route(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if not user or not user[5]:  # interests
        await message.answer("Сначала укажите ваши интересы в настройках!")
        return

    # Получаем предыдущее количество объектов или ставим 5 по умолчанию
    route = get_user_route(message.from_user.id)
    count = len(route) if route and len(route) > 0 else 5

    await message.answer(f"Создаю новый маршрут с {count} объектами...")

    # Generate route using DeepSeek
    route = get_route_from_deepseek(user[5], count)

    if route:
        update_user_route(message.from_user.id, route)
        update_route_step(message.from_user.id, 0)

        route_text = "Новый маршрут:\n\n"
        for i, obj in enumerate(route, 1):
            route_text += f"{i}. {obj['name']}\n   {obj['description']}\n"
            route_text += f"   Координаты: {format_coordinates(obj['latitude'], obj['longitude'])}\n\n"

        await message.answer(route_text, reply_markup=get_route_settings_keyboard())
        await state.set_state(UserStates.on_route)
    else:
        await message.answer("Не удалось создать маршрут. Попробуйте позже.", reply_markup=get_main_keyboard())
        await state.clear()


@router.message(F.text == "👤 Мой профиль")
async def show_profile(message: Message):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала зарегистрируйтесь с помощью /start")
        return

    # Получаем информацию о текущем маршруте
    route = get_user_route(message.from_user.id)
    step = get_route_step(message.from_user.id)

    profile_text = f"""
👤 Профиль:
Имя: {user[2]}
Телефон: {user[3]}
Баллы: {user[4]}

📊 Статистика:
- Посещенные объекты: {len(user[7]) if user[7] else 0}
"""

    # Добавляем информацию о текущем маршруте
    if route and len(route) > 0:
        if step < len(route):
            current_object = route[step]
            profile_text += f"\n🧭 Текущий маршрут: {len(route)} объектов\n"
            profile_text += f"📍 Текущий объект: {current_object['name']} ({step + 1}/{len(route)})"
        else:
            profile_text += f"\n✅ Маршрут завершен: {len(route)} объектов"

    await message.answer(profile_text, reply_markup=get_profile_keyboard())


@router.message(F.text == "📊 Мои баллы")
async def show_points(message: Message):
    user = get_user(message.from_user.id)
    if user:
        await message.answer(f"Ваши баллы: {user[4]}", reply_markup=get_main_keyboard())


@router.message(F.text == "🏪 Магазин")
async def show_shop(message: Message):
    items = get_shop_items()
    if not items:
        await message.answer("В магазине пока нет товаров", reply_markup=get_main_keyboard())
        return

    shop_text = "🏪 Магазин:\n\n"
    for item in items:
        shop_text += f"{item[1]} - {item[3]} баллов\n{item[2]}\n\n"

    await message.answer(shop_text, reply_markup=get_shop_keyboard())


@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message):
    await message.answer("⚙️ Настройки:", reply_markup=get_settings_keyboard())


@router.message(F.text == "✏️ Изменить интересы")
async def change_interests(message: Message, state: FSMContext):
    await message.answer("Введите новые интересы:")
    await state.set_state(UserStates.changing_interests)


@router.message(F.text == "📱 Изменить телефон")
async def change_phone(message: Message, state: FSMContext):
    await message.answer("Введите новый номер телефона:")
    await state.set_state(UserStates.changing_phone)


@router.message(UserStates.changing_phone)
async def process_phone_change(message: Message, state: FSMContext):
    # In a real app, you would update the phone in the database
    await message.answer("Номер телефона обновлен!", reply_markup=get_main_keyboard())
    await state.clear()


@router.message(F.text == "🔙 Назад")
async def go_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Выберите действие:", reply_markup=get_main_keyboard())


# Fallback handler
@router.message()
async def fallback(message: Message):
    await message.answer("Не понимаю команду. Выберите действие:", reply_markup=get_main_keyboard())