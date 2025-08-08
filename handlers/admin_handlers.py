import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from datetime import datetime

from config import ADMIN_IDS, States
from keyboards import (
    create_admin_keyboard,
    create_order_status_keyboard,
    create_back_to_admin_keyboard,
    create_order_list_keyboard
)
from database import db

router = Router()

# Добавляем синхронизацию админов при старте
def sync_admins():
    """Синхронизирует админов из config.py с базой данных"""
    for admin_id in ADMIN_IDS:
        if admin_id not in db.admins:
            db.admins.append(admin_id)
    db.save()

# Вызываем при импорте
sync_admins()

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not db.is_admin(message.from_user.id):
        return  # Полное игнорирование для не-админов
    
    try:
        # Удаляем предыдущие сообщения с админ-панелью
        await message.delete()
    except:
        pass
        
    try:
        # Отправляем одно сообщение с панелью
        await message.answer(
            "👨‍💻 Панель администратора",
            reply_markup=create_admin_keyboard()
        )
    except Exception as e:
        logging.error(f"Ошибка админ-панели: {e}")

@router.callback_query(F.data.startswith("admin_all_orders"))
async def admin_all_orders(callback: CallbackQuery):
    await show_admin_orders_page(callback, 1)

async def show_admin_orders_page(callback: CallbackQuery, page: int):
    if not db.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    orders_data = db.get_all_orders_paginated(page)
    
    if not orders_data["orders"]:
        await callback.answer("📭 Нет заказов на этой странице", show_alert=True)
        return
    
    text = f"📋 Все заказы (страница {page} из {orders_data['pages']}):\n\n"
    for order in orders_data["orders"]:
        user = db.users.get(str(order["user_id"]), {})
        status_emoji = {
            "ожидает оплаты": "🟡",
            "ожидает проверки": "🟠",
            "в работе": "🔵",
            "выполнен": "🟢",
            "отменён": "🔴"
        }.get(order["status"], "⚪️")
        
        created_at = datetime.fromisoformat(order["created_at"]).strftime("%d.%m.%Y %H:%M")
        
        text += (
            f"🆔 Заказ: {order['id']}\n"
            f"👤 Пользователь: @{user.get('username', 'N/A')} (ID: {order['user_id']})\n"
            f"🎮 Игра: {order['game']}\n"
            f"💎 Валюта: {order['currency']} - {order['amount']}₽\n"
            f"💳 Метод: {order.get('payment_method', 'не указан')}\n"
            f"📅 Дата: {created_at}\n"            
            f"{status_emoji} Статус: {order['status']}\n\n"
        )
    
    # Изменяем существующее сообщение вместо отправки нового
    await callback.message.edit_text(
        text=text,
        reply_markup=create_order_list_keyboard(
            orders_data["orders"],
            orders_data["page"],
            orders_data["pages"],
            is_admin=True
        )
    )

@router.callback_query(F.data.startswith("admin_orders_page_"))
async def handle_admin_orders_pagination(callback: CallbackQuery):
    if not db.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    try:
        page = int(callback.data.split("_")[-1])
        await show_admin_orders_page(callback, page)
    except Exception as e:
        logging.error(f"Ошибка пагинации: {e}")
        await callback.answer("❌ Ошибка загрузки страницы", show_alert=True)


@router.callback_query(F.data.startswith("admin_order_detail_"))
async def admin_show_order_detail(callback: CallbackQuery):
    if not db.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    order_id = callback.data.split("_")[-1]
    order = db.orders.get(order_id)
    
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    
    user = db.users.get(str(order["user_id"]), {})
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
        f"👤 Пользователь: @{user.get('username', 'N/A')} (ID: {order['user_id']})\n"
        f"🎮 Игра: {order['game']}\n"
        f"💎 Валюта: {order['currency']}\n"
        f"💰 Сумма: {order['amount']}₽\n"
        f"🆔 Игровой ID: {order['game_id']}\n"
        f"💳 Метод оплаты: {order.get('payment_method', 'не указан')}\n"
        f"📅 Создан: {created_at}\n"
        f"🔄 Обновлен: {updated_at}\n"
        f"{status_emoji} Статус: {order['status']}\n\n"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 В работе", callback_data=f"admin_status_work_{order_id}"),
                InlineKeyboardButton(text="✅ Выполнен", callback_data=f"admin_status_done_{order_id}"),
            ],
            [
                InlineKeyboardButton(text="🔙 К списку заказов", callback_data="admin_orders_page_1")
            ]
        ])
    )

@router.callback_query(F.data.startswith("admin_status_"))
async def admin_change_order_status(callback: CallbackQuery):
    if not db.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    # Определяем новый статус
    if callback.data.startswith("admin_status_work_"):
        order_id = callback.data[18:]
        new_status = "в работе"
        status_text = "в работу"
    elif callback.data.startswith("admin_status_done_"):
        order_id = callback.data[18:]
        new_status = "выполнен"
        status_text = "выполнен"
    else:
        await callback.answer("Неизвестная команда", show_alert=True)
        return
    
    # Обновляем статус заказа
    if not db.update_order_status(order_id, new_status):
        await callback.answer("❌ Ошибка изменения статуса", show_alert=True)
        return
    
    order = db.orders.get(order_id)
    if not order:
        await callback.answer("❌ Заказ не найден", show_alert=True)
        return
    
    # Уведомляем пользователя
    try:
        await callback.bot.send_message(
            chat_id=order["user_id"],
            text=f"🔄 Статус вашего заказа #{order_id} изменен на '{new_status}'\n\n"
                 f"🎮 Игра: {order['game']}\n"
                 f"💎 Валюта: {order['currency']}\n"
                 f"💰 Сумма: {order['amount']}₽\n\n"
                 f"Если у вас есть вопросы, обратитесь к администратору."
        )
    except Exception as e:
        logging.error(f"Не удалось уведомить пользователя {order['user_id']}: {e}")
        await callback.answer(f"✅ Статус изменен, но не удалось уведомить пользователя", show_alert=True)
    else:
        await callback.answer(f"✅ Статус изменен на '{new_status}'", show_alert=False)
    
    # Обновляем сообщение с деталями заказа
    await admin_show_order_detail(callback)

@router.callback_query(F.data.startswith("status_"))
async def change_order_status(callback: CallbackQuery):
    if callback.data.startswith("status_work_"):
        order_id = callback.data[12:]
        if db.update_order_status(order_id, "в работе"):
            await callback.message.edit_text(
                f"✅ Статус заказа {order_id} изменён на 'в работе'",
                reply_markup=create_back_to_admin_keyboard()
            )
    elif callback.data.startswith("status_done_"):
        order_id = callback.data[12:]
        if db.update_order_status(order_id, "выполнен"):
            await callback.message.edit_text(
                f"✅ Статус заказа {order_id} изменён на 'выполнен'",
                reply_markup=create_back_to_admin_keyboard()
            )

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📢 Введите сообщение для рассылки всем пользователям:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Отменить", callback_data="admin_back")]
        ])
    )
    await state.set_state(States.AWAITING_BROADCAST)

@router.message(StateFilter(States.AWAITING_BROADCAST))
async def admin_broadcast_send(message: Message, state: FSMContext, bot):
    users = db.users.keys()
    success = 0
    failed = 0
    
    for user_id in users:
        try:
            await bot.send_message(
                chat_id=int(user_id),
                text=f"📢 Сообщение от администратора:\n\n{message.text}"
            )
            success += 1
        except Exception as e:
            print(f"Ошибка рассылки для {user_id}: {e}")
            failed += 1
    
    await message.answer(
        f"📢 Рассылка завершена:\nУспешно: {success}\nНе удалось: {failed}"
    )
    await state.clear()

@router.callback_query(F.data == "admin_message_user")
async def admin_message_user_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "✉️ Введите ID пользователя, которому хотите написать:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Отменить", callback_data="admin_back")]
        ])
    )
    await state.set_state(States.AWAITING_USER_MESSAGE)

@router.message(StateFilter(States.AWAITING_USER_MESSAGE))
async def admin_message_user_get_id(message: Message, state: FSMContext):
    try:
        user_id = int(message.text)
        await state.update_data(target_user_id=user_id)
        await message.answer(
            "Введите сообщение для этого пользователя:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Отменить", callback_data="admin_back")]
            ])
        )
        await state.set_state("awaiting_user_message_text")
    except ValueError:
        await message.answer("Некорректный ID пользователя. Введите число.")

@router.message(StateFilter("awaiting_user_message_text"))
async def admin_message_user_send(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    user_id = data.get("target_user_id")
    
    if not user_id:
        await message.answer("Ошибка: пользователь не указан")
        await state.clear()
        return
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"✉️ Сообщение от администратора:\n\n{message.text}"
        )
        await message.answer("✅ Сообщение отправлено")
    except Exception as e:
        await message.answer(f"❌ Не удалось отправить сообщение: {e}")
    
    await state.clear()

@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "👨‍💻 Панель администратора",
        reply_markup=create_admin_keyboard()
    )