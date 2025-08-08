from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import GAMES

def create_game_keyboard() -> InlineKeyboardMarkup:
    games = list(GAMES.keys())
    keyboard = []
    
    for i in range(0, len(games), 2):
        row = []
        if i < len(games):
            row.append(InlineKeyboardButton(text=games[i], callback_data=f"game_{games[i]}"))
        if i + 1 < len(games):
            row.append(InlineKeyboardButton(text=games[i+1], callback_data=f"game_{games[i+1]}"))
        if row:
            keyboard.append(row)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_currency_keyboard(game: str) -> InlineKeyboardMarkup:
    currencies = list(GAMES[game].items())
    keyboard = []
    
    for i in range(0, len(currencies), 2):
        row = []
        if i < len(currencies):
            currency, price = currencies[i]
            row.append(InlineKeyboardButton(
                text=f"{currency} - {price}₽",
                callback_data=f"currency_{i}"
            ))
        if i + 1 < len(currencies):
            currency, price = currencies[i+1]
            row.append(InlineKeyboardButton(
                text=f"{currency} - {price}₽",
                callback_data=f"currency_{i+1}"
            ))
        if row:
            keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="back_to_games"
    )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_yes"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="confirm_no")
        ]
    ])

def create_payment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплата USDT", callback_data="payment_usdt")],
        [InlineKeyboardButton(text="💳 Оплата TON", callback_data="payment_ton")],
        [InlineKeyboardButton(text="🏦 Банковские реквизиты", callback_data="payment_bank")],
        [InlineKeyboardButton(text="❌ Отменить заказ", callback_data="cancel_order")]
    ])

def create_ton_payment_keyboard(order_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"paid_ton_{order_id}")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order")]
    ])

def create_usdt_payment_keyboard(order_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"paid_usdt_{order_id}")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order")]
    ])

def create_bank_payment_keyboard(order_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"paid_bank_{order_id}")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order")]
    ])

def create_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Все заказы", callback_data="admin_all_orders")],
        [InlineKeyboardButton(text="📩 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="✉️ Написать пользователю", callback_data="admin_message_user")]
    ])

def create_order_status_keyboard(order_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 В работе", callback_data=f"status_work_{order_id}")],
        [InlineKeyboardButton(text="✅ Выполнен", callback_data=f"status_done_{order_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])

def create_back_to_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 В админ-панель", callback_data="admin_back")]
    ])


def create_pagination_keyboard(page: int, pages: int, prefix: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру пагинации"""
    keyboard = []
    
    # Кнопки навигации
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{prefix}_{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{pages}", callback_data="current_page"))
    
    if page < pages:
        nav_buttons.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"{prefix}_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_order_list_keyboard(orders: list, page: int, pages: int, is_admin: bool = False) -> InlineKeyboardMarkup:
    """Создает клавиатуру со списком заказов"""
    keyboard = []
    
    # Кнопки заказов
    for order in orders:
        prefix = "admin_" if is_admin else ""
        keyboard.append([
            InlineKeyboardButton(
                text=f"Заказ #{order['id']} - {order['status']}",
                callback_data=f"{prefix}order_detail_{order['id']}"
            )
        ])
    
    # Кнопки пагинации
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{prefix}orders_page_{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{pages}", callback_data="current_page"))
    
    if page < pages:
        nav_buttons.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"{prefix}orders_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Кнопка назад для админа
    keyboard.append([InlineKeyboardButton(
        text="🔙 В админ-панель" if is_admin else "🔙 На главную",
        callback_data="admin_back" if is_admin else "back_to_start"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)