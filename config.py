import os
from dotenv import load_dotenv
from typing import Dict, List

os.makedirs("data", exist_ok=True)
load_dotenv()

# Основные настройки
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]

# Добавим API для получения курса TON:
USDT_API_URL = "https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=rub"
TON_API_URL = "https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=rub"

# Платежные реквизиты
USDT_WALLET = os.getenv("USDT_WALLET")
TON_WALLET = os.getenv("TON_WALLET")
# TON_WALLET = os.getenv("TON_WALLET")
BANK_DETAILS = os.getenv("BANK_DETAILS", """
Реквизиты для оплаты:
Т-Банк
Номер карты: 2200 7013 5987 4903
Получатель: Алексей М.
""")

# Список игр и валюты
GAMES = {
    "Mobile Legends: Bang Bang": {
        "8 алмазов": 15.9,
        "32+3 алмазов": 69,
        "80+8 алмазов": 175,
        "120+12 алмазов": 262,
        "239+25 алмазов": 525,
        "396+44 алмазов": 870,
        "633+101 алмазов": 1399,
        "791+142 алмазов": 1720,
        "1186+224 алмазов": 2599,
        "1581+300 алмазов": 3499,
        "2371+474 алмазов": 5299,
        "5136+1027 алмазов": 11299,
        "Алмазный пропуск (неделя)": 199,
        "50+50 (первое пополнение)": 139,
        "150+150 (первое пополнение)": 345,
        "250+250 (первое пополнение)": 560,
        "500+500 (первое пополнение)": 1150
    },
    "Free Fire": {
        "100+5": 75,
        "310+16": 240,
        "520+26": 360,
        "1060+53": 750,
        "2180+218": 1520,
        "5600+560": 3850,
        "Ваучер на неделю": 149
    },
    "Standoff 2": {
        "100": 135,
        "500": 520,
        "1000": 945,
        "3000": 2125,
        "Gold Pass": 860,
        "+1 уровень": 112,
        "+10 уровней": 840,
        "+25 уровней": 1855,
        "+50 уровней": 3890,
        "+75 уровней": 4750
    },
    "Rush Royale": {
        "500 + 50 Кристаллов": 990,
        "1000 + 100 Кристаллов": 1955,
        "2500 + 250 Кристаллов": 4850,
        "5500 + 550 Кристаллов": 9790,
        "Эпический пропуск": 470,
        "Легендарный пропуск": 1200,
        "Премиум 10 дней": 720,
        "Премиум 30 дней": 1410
    },
    "Super Sus": {
        "100": 65,
        "310": 179,
        "520": 299,
        "1060": 589,
        "2180": 1250,
        "5600": 2990,
        "Еженедельная Карта": 65,
        "Ежемесячная Карта": 750,
        "Супер ВИП Карта": 850,
        "Супер пропуск": 299,
        "Набор Super Pass": 560
    },
    "ВКонтакте": {
        "1 голос": 7.5
    },
    "Русская Рыбалка": {
        "1 золото": 110,
        "5 золота": 499,
        "10 золота": 970,
        "20 золота": 1890,
        "50 золота": 4490,
        "100 золота": 8750,
        "200 золота": 17500,
        "500 золота": 42000,
        "Премиум 3 дня": 135,
        "Премиум 7 дней": 240,
        "Премиум 30 дней": 560,
        "Премиум 90 дней": 1490,
        "Премиум 180 дней": 2700,
        "Премиум 360 дней": 4900,
        "Бессрочный премиум": 75000
    }
}


# Состояния FSM
class States:
    SELECT_GAME = "select_game"
    SELECT_CURRENCY = "select_currency"
    ENTER_GAME_ID = "enter_game_id"
    CONFIRM_ORDER = "confirm_order"
    PAYMENT = "payment"
    AWAITING_BROADCAST = "awaiting_broadcast"
    AWAITING_USER_MESSAGE = "awaiting_user_message"
    AWAITING_USER_MESSAGE_TEXT = "awaiting_user_message_text"