from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from datetime import datetime

from config import GAMES, States, TON_WALLET, BANK_DETAILS, TON_API_URL, USDT_WALLET, USDT_API_URL
from keyboards import (
    create_game_keyboard,
    create_currency_keyboard,
    create_confirmation_keyboard,
    create_payment_keyboard,
    create_ton_payment_keyboard,
    create_bank_payment_keyboard,
    create_order_status_keyboard,
    create_order_list_keyboard,
    create_usdt_payment_keyboard
)
from database import db
import requests
import logging

router = Router()

async def get_ton_rate() -> float:
    """Получает текущий курс TON к рублю"""
    try:
        response = requests.get(TON_API_URL)
        response.raise_for_status()
        data = response.json()
        return data["the-open-network"]["rub"]
    except Exception as e:
        logging.error(f"Ошибка получения курса TON: {e}")
        return 235.0  # Значение по умолчанию

async def get_usdt_rate() -> float:
    """Получает текущий курс USDT к рублю"""
    try:
        response = requests.get(USDT_API_URL)
        response.raise_for_status()
        data = response.json()
        return data["tether"]["rub"]
    except Exception as e:
        logging.error(f"Ошибка получения курса USDT: {e}")
        return 81.0  # Значение по умолчанию

@router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    user = message.from_user
    db.add_user(user.id, user.username or "", user.first_name or "")
    await message.answer(
        "🎮 Добро пожаловать в бота по продаже игровой валюты!",
        reply_markup=create_game_keyboard()
    )
    await state.set_state(States.SELECT_GAME)

@router.callback_query(F.data == "back_to_games", StateFilter(States.SELECT_CURRENCY))
async def back_to_games(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите игру из списка:",
        reply_markup=create_game_keyboard()
    )
    await state.set_state(States.SELECT_GAME)

@router.callback_query(F.data.startswith("game_"), StateFilter(States.SELECT_GAME))
async def select_game(callback: CallbackQuery, state: FSMContext):
    game = callback.data.split("_")[1]
    await state.update_data(game=game)
    await callback.message.edit_text(
        f"🎮 Игра: {game}\n\nВыберите количество валюты:",
        reply_markup=create_currency_keyboard(game)
    )
    await state.set_state(States.SELECT_CURRENCY)

@router.callback_query(F.data.startswith("currency_"), StateFilter(States.SELECT_CURRENCY))
async def select_currency(callback: CallbackQuery, state: FSMContext):
    idx = int(callback.data.split("_")[1])
    data = await state.get_data()
    game = data["game"]
    currency, price = list(GAMES[game].items())[idx]
    
    await state.update_data(currency=currency, price=price)
    await callback.message.edit_text(
        f"🎮 Игра: {game}\n💎 Валюта: {currency} - {price}₽\n\n"
        "Введите ваш игровой ID:"
    )
    await state.set_state(States.ENTER_GAME_ID)

@router.message(StateFilter(States.ENTER_GAME_ID))
async def enter_game_id(message: Message, state: FSMContext):
    game_id = message.text.strip()
    if not game_id:
        await message.answer("Пожалуйста, введите корректный игровой ID")
        return
    
    data = await state.get_data()
    game = data["game"]
    currency = data["currency"]
    price = data["price"]
    
    await state.update_data(game_id=game_id)
    await message.answer(
        f"🔍 Проверьте данные заказа:\n\n"
        f"🎮 Игра: {game}\n"
        f"💎 Валюта: {currency}\n"
        f"💰 Сумма: {price}₽\n"
        f"🆔 Игровой ID: {game_id}\n\n"
        "Всё верно?",
        reply_markup=create_confirmation_keyboard()
    )
    await state.set_state(States.CONFIRM_ORDER)

@router.callback_query(F.data == "confirm_no", StateFilter(States.CONFIRM_ORDER))
async def confirm_no(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Заказ отменён. Выберите игру из списка:",
        reply_markup=create_game_keyboard()
    )
    await state.set_data({})
    await state.set_state(States.SELECT_GAME)

@router.callback_query(F.data == "confirm_yes", StateFilter(States.CONFIRM_ORDER))
async def confirm_yes(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order = db.add_order(
        user_id=callback.from_user.id,
        game=data["game"],
        currency=data["currency"],
        amount=data["price"],
        game_id=data["game_id"],
        payment_method=None  # Пока неизвестен, установится при оплате
    )
    
    await state.update_data(order_id=order["id"])
    await callback.message.edit_text(
        f"💰 К оплате: {data['price']}₽\n\n"
        "Выберите способ оплаты:",
        reply_markup=create_payment_keyboard()
    )
    await state.set_state(States.PAYMENT)

@router.callback_query(F.data == "payment_ton", StateFilter(States.PAYMENT))
async def payment_ton(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    ton_rate = await get_ton_rate()
    ton_amount = data['price'] / ton_rate
    
    await callback.message.edit_text(
        f"💳 Оплата через TON\n\n"
        f"Сумма: {data['price']}₽ (~{ton_amount:.2f} TON)\n"
        f"Курс: 1 TON = {ton_rate:.2f}₽\n"
        f"Кошелек: {TON_WALLET}\n\n"
        "1. Откройте @wallet в Telegram\n"
        "2. Переведите указанную сумму\n"
        "3. Нажмите кнопку 'Я оплатил'\n\n"
        f"ID вашего заказа: {data['order_id']}",
        reply_markup=create_ton_payment_keyboard(data['order_id'])
    )

@router.callback_query(F.data == "payment_usdt", StateFilter(States.PAYMENT))
async def payment_usdt(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    usdt_rate = await get_usdt_rate()
    usdt_amount = data['price'] / usdt_rate
    
    await callback.message.edit_text(
        f"💳 Оплата через USDT (TRC20)\n\n"
        f"Сумма: {data['price']}₽ (~{usdt_amount:.2f} USDT)\n"
        f"Курс: 1 USDT = {usdt_rate:.2f}₽\n"
        f"Кошелек: {USDT_WALLET}\n\n"
        "1. Переведите указанную сумму\n"
        "2. Нажмите кнопку 'Я оплатил'\n\n"
        f"ID вашего заказа: {data['order_id']}",
        reply_markup=create_usdt_payment_keyboard(data['order_id'])
    )

@router.callback_query(F.data == "payment_bank", StateFilter(States.PAYMENT))
async def payment_bank(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.edit_text(
        f"🏦 Оплата по реквизитам\n\n"
        f"Сумма: {data['price']}₽\n"
        f"{BANK_DETAILS}\n\n"
        "После оплаты нажмите кнопку 'Я оплатил'\n\n"
        f"ID вашего заказа: {data['order_id']}",
        reply_markup=create_bank_payment_keyboard(data['order_id'])
    )

@router.callback_query(F.data.startswith("paid_"))
async def paid(callback: CallbackQuery, state: FSMContext):
    """Обработчик подтверждения оплаты для всех методов"""
    try:
        bot = callback.bot
        parts = callback.data.split("_")
        if len(parts) != 3:
            await callback.answer("❌ Ошибка в данных заказа", show_alert=True)
            return
        
        payment_type = parts[1]  # ton, usdt или bank
        order_id = parts[2]
        
        payment_method = {
            "ton": "TON",
            "usdt": "USDT",
            "bank": "Банк"
        }.get(payment_type, "неизвестно")
        
        # Обновляем заказ
        if not db.update_order(order_id, {
            "status": "ожидает проверки",
            "payment_method": payment_method,
            "updated_at": datetime.now().isoformat()
        }):
            await callback.answer("❌ Ошибка обновления заказа", show_alert=True)
            return
        
        # Получаем данные заказа
        order = db.orders.get(order_id)
        if not order:
            await callback.answer("❌ Заказ не найден", show_alert=True)
            return
        
        # Формируем уведомление для админов
        user = db.users.get(str(order["user_id"]), {})
        created_at = datetime.fromisoformat(order["created_at"]).strftime("%d.%m.%Y %H:%M")
        
        text = (
            "🛒 Новый оплаченный заказ!\n\n"
            f"🆔 ID заказа: {order['id']}\n"
            f"💳 Метод оплаты: {payment_method}\n"
            f"🎮 Игра: {order['game']}\n"
            f"💎 Валюта: {order['currency']}\n"
            f"💰 Сумма: {order['amount']}₽\n"
            f"🆔 Игровой ID: {order['game_id']}\n"
            f"👤 Покупатель: @{user.get('username', 'N/A')}\n"
            f"📅 Время заказа: {created_at}"
        )
        
        # Отправляем уведомления админам
        for admin_id in db.admins:
            try:
                await bot.send_message(
                    chat_id=admin_id, 
                    text=text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="🔄 В работе", callback_data=f"admin_status_work_{order_id}"),
                            InlineKeyboardButton(text="✅ Выполнен", callback_data=f"admin_status_done_{order_id}"),
                        ]
                    ])
                )
            except Exception as e:
                logging.error(f"Ошибка уведомления админа {admin_id}: {e}")
        
        # Ответ пользователю
        await callback.message.edit_text(
            "✅ Спасибо за оплату! Ваш заказ принят в обработку.\n"
            "Вы можете проверить статус заказа командой /myorders"
        )
        await state.clear()
        
    except Exception as e:
        logging.error(f"Ошибка в обработчике оплаты: {e}")
        await callback.answer("❌ Произошла ошибка при обработке оплаты", show_alert=True)

@router.callback_query(F.data == "cancel_order", StateFilter(States.PAYMENT))
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if "order_id" in data:
        db.update_order_status(data["order_id"], "отменён")
    
    await callback.message.edit_text(
        "Заказ отменён. Выберите игру из списка:",
        reply_markup=create_game_keyboard()
    )
    await state.clear()
    await state.set_state(States.SELECT_GAME)

@router.message(Command("myorders"))
async def my_orders(message: Message, state: FSMContext):
    await show_orders_page(message, message.from_user.id, 1)

async def show_orders_page(message: Message, user_id: int, page: int):
    orders_data = db.get_user_orders_paginated(user_id, page)
    
    if not orders_data["orders"]:
        await message.answer("У вас пока нет заказов.")
        return
    
    text = f"📋 Ваши заказы (страница {page} из {orders_data['pages']}):\n\n"
    for order in orders_data["orders"]:
        status_emoji = {
            "ожидает оплаты": "🟡",
            "ожидает проверки": "🟠",
            "в работе": "🔵",
            "выполнен": "🟢",
            "отменён": "🔴"
        }.get(order["status"], "⚪️")
        
        created_at = datetime.fromisoformat(order["created_at"]).strftime("%d.%m.%Y %H:%M")
        
        text += (
            f"🆔 ID заказа: {order['id']}\n"
            f"🎮 Игра: {order['game']}\n"
            f"💎 Валюта: {order['currency']} - {order['amount']}₽\n"
            f"📅 Дата: {created_at}\n"
            f"{status_emoji} Статус: {order['status']}\n\n"
        )
    
    await message.answer(
        text,
        reply_markup=create_order_list_keyboard(
            orders_data["orders"],
            orders_data["page"],
            orders_data["pages"]
        )
    )

@router.callback_query(F.data.startswith("orders_page_"))
async def handle_orders_pagination(callback: CallbackQuery):
    page = int(callback.data.split("_")[-1])
    await callback.message.delete()
    await show_orders_page(callback.message, callback.from_user.id, page)

@router.callback_query(F.data == "back_to_start")
async def back_to_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()  # Удаляем предыдущее сообщение
    await callback.message.answer(  # Отправляем новое сообщение
        "🎮 Добро пожаловать в бота по продаже игровой валюты!",
        reply_markup=create_game_keyboard()
    )
    await state.set_state(States.SELECT_GAME)

@router.callback_query(F.data.startswith("order_detail_"))
async def show_order_detail(callback: CallbackQuery):
    order_id = callback.data.split("_")[-1]
    order = db.orders.get(order_id)
    
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    
    status_emoji = {
        "ожидает оплаты": "🟡",
        "ожидает проверки": "🟠",
        "в работе": "🔵",
        "выполнен": "🟢",
        "отменён": "🔴"
    }.get(order["status"], "⚪️")
    
    created_at = datetime.fromisoformat(order["created_at"]).strftime("%d.%m.%Y %H:%M")
    updated_at = datetime.fromisoformat(order["updated_at"]).strftime("%d.%m.%Y %H:%M")
    
    text = (
        f"📋 Детали заказа #{order['id']}\n\n"
        f"🎮 Игра: {order['game']}\n"
        f"💎 Валюта: {order['currency']}\n"
        f"💰 Сумма: {order['amount']}₽\n"
        f"💳 Метод оплаты: {order.get('payment_method', 'не указан')}\n"
        f"🆔 Игровой ID: {order['game_id']}\n"
        f"📅 Создан: {created_at}\n"
        f"🔄 Обновлен: {updated_at}\n"
        f"{status_emoji} Статус: {order['status']}\n\n"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К списку заказов", callback_data="orders_page_1")]
        ])
    )

