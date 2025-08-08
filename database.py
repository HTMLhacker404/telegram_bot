import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
from config import ADMIN_IDS  # Добавляем импорт

class Database:
    def __init__(self):
        self.data_path = "data/data.json"
        self._ensure_data_dir()
        self.admins = ADMIN_IDS.copy()  # Копируем список админов из config.py
        self._load_data()
    
    def _ensure_data_dir(self):
        """Создает директорию data, если она не существует"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.data_path):
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump({
                    "users": {},
                    "orders": {},
                    "admins": ADMIN_IDS.copy(),  # Сохраняем админов при создании файла
                    "last_order_id": 0
                }, f)
    
    def _load_data(self):
        """Загружает данные из файла"""
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.users = data.get("users", {})
                self.orders = data.get("orders", {})
                # Объединяем админов из config и базы данных
                self.admins = list(set(self.admins + data.get("admins", [])))
                self.last_order_id = data.get("last_order_id", 0)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Ошибка загрузки данных: {e}")
            self.users = {}
            self.orders = {}
            # self.admins уже инициализирован через ADMIN_IDS
            self.last_order_id = 0
            self.save()
    
    def save(self):
        """Сохраняет данные в файл"""
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump({
                "users": self.users,
                "orders": self.orders,
                "admins": self.admins,
                "last_order_id": self.last_order_id
            }, f, ensure_ascii=False, indent=2)
    
    def add_user(self, user_id: int, username: str, first_name: str):
        """Добавляет нового пользователя"""
        user_id_str = str(user_id)
        if user_id_str not in self.users:
            self.users[user_id_str] = {
                "username": username,
                "first_name": first_name,
                "created_at": datetime.now().isoformat()
            }
            self.save()
    
    def add_order(self, user_id: int, game: str, currency: str, amount: float, game_id: str, payment_method: str = None) -> Dict:
        """Добавляет новый заказ"""
        self.last_order_id += 1
        order_id = str(self.last_order_id)
        
        order = {
            "id": order_id,
            "user_id": user_id,
            "game": game,
            "currency": currency,
            "amount": amount,
            "game_id": game_id,
            "payment_method": payment_method,  # Добавлено
            "status": "ожидает оплаты",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.orders[order_id] = order
        self.save()
        return order
    
    def update_order(self, order_id: str, update_data: dict) -> bool:
        """Обновляет любые данные заказа"""
        if order_id in self.orders:
            self.orders[order_id].update(update_data)
            self.orders[order_id]["updated_at"] = datetime.now().isoformat()
            self.save()
            return True
        return False

    # И модифицируйте существующий метод:
    def update_order_status(self, order_id: str, status: str) -> bool:
        """Обновляет только статус (для обратной совместимости)"""
        return self.update_order(order_id, {"status": status})
    
    def get_user_orders(self, user_id: int) -> List[Dict]:
        """Возвращает заказы пользователя"""
        return [
            order for order in self.orders.values() 
            if order["user_id"] == user_id
        ]
    
    def get_all_orders(self) -> List[Dict]:
        """Возвращает все заказы"""
        return list(self.orders.values())
    
    def is_admin(self, user_id: int) -> bool:
        """Проверка прав администратора с логированием"""
        result = user_id in self.admins
        if not result:
            logging.warning(f"Попытка доступа неадмина: {user_id}. Админы: {self.admins}")
        return result
    
    def sync_with_config_admins(self, config_admins: list):
        """Синхронизирует список админов с конфигом"""
        # Приводим оба списка к int для сравнения
        db_admins = [int(x) for x in self.admins]
        config_admins = [int(x) for x in config_admins]
        
        # Объединяем списки без дубликатов
        combined = list(set(db_admins + config_admins))
        
        # Обновляем список в базе данных
        self.admins = combined
        self.save()
        
        logging.info(f"Синхронизированы админы. Итоговый список: {self.admins}")
    
    def get_user_orders_paginated(self, user_id: int, page: int = 1, per_page: int = 5) -> dict:
        """Возвращает заказы пользователя с пагинацией"""
        all_orders = [
            order for order in self.orders.values() 
            if order["user_id"] == user_id
        ]
        total = len(all_orders)
        pages = (total + per_page - 1) // per_page
        start = (page - 1) * per_page
        end = start + per_page
        
        return {
            "orders": sorted(all_orders, key=lambda x: x["created_at"], reverse=True)[start:end],
            "page": page,
            "pages": pages,
            "total": total
        }

    def get_all_orders_paginated(self, page: int = 1, per_page: int = 10) -> dict:
        """Возвращает все заказы с пагинацией"""
        all_orders = list(self.orders.values())
        total = len(all_orders)
        pages = (total + per_page - 1) // per_page
        start = (page - 1) * per_page
        end = start + per_page
        
        return {
            "orders": sorted(all_orders, key=lambda x: x["created_at"], reverse=True)[start:end],
            "page": page,
            "pages": pages,
            "total": total
        }

print(f"Инициализация базы данных. Админы: {ADMIN_IDS}")
# Инициализация базы данных
db = Database()