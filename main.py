import telebot
from telebot import types
import json
import datetime
import os
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

# === НАСТРОЙКИ ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # <-- используем os.environ.get
if not BOT_TOKEN:
    raise Exception("❌ BOT_TOKEN не найден. Проверь настройки Environment Variables в Render!")

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", 
# Продавцы
SELLERS = {
    "sssaaiidddd": "Саид",
    "Yagona771": "Нилюфар",
    "Chayka2288": "Оксана"
}

# Категории
CATEGORIES = [
    "Электрика", "Сантехника", "Финишная отделка", "Крепеж", "Инструмент",
    "Товары для дома", "Канцтовары", "Кошкин дом", "Парфюмерия",
    "Бытовая химия", "Косметика", "Аксессуары для мобильных", "Прочее"
]

DATA_FILE = "orders.json"
TIMEZONE = pytz.timezone("Asia/Tashkent")

bot = telebot.TeleBot(BOT_TOKEN)

# === ХРАНЕНИЕ ДАННЫХ ===
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {cat: [] for cat in CATEGORIES}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()
activity = {}

# === ОБРАБОТЧИКИ ===
@bot.message_handler(commands=['start'])
def start(msg):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in CATEGORIES:
        kb.add(types.KeyboardButton(cat))
    bot.send_message(msg.chat.id, "Выберите категорию для добавления товара:", reply_markup=kb)

@bot.message_handler(func=lambda msg: msg.text in CATEGORIES)
def choose_category(msg):
    bot.send_message(msg.chat.id, f"Введите название товара для категории '{msg.text}':")
    bot.register_next_step_handler(msg, lambda m: add_item(m, msg.text))

def add_item(msg, category):
    username = msg.from_user.username or "неизвестный"
    item = msg.text.strip()
    if not item:
        return bot.send_message(msg.chat.id, "Пустое значение, повторите попытку.")
    
    data[category].append(f"{item} — добавил {username}")
    save_data(data)

    # Учитываем активность
    if username not in activity:
        activity[username] = 0
    activity[username] += 1

    bot.send_message(msg.chat.id, f"✅ Товар '{item}' добавлен в '{category}'!")

# === ОТЧЁТ ПО ВТОРНИКАМ ===
def weekly_report():
    now = datetime.datetime.now(TIMEZONE)
    if now.weekday() == 1 and now.hour == 21:  # вторник 21:00
        report = "🧾 Еженедельный отчёт по заказам:\n\n"
        for cat, items in data.items():
            if items:
                report += f"📦 *{cat}*\n" + "\n".join(f"- {i}" for i in items) + "\n\n"
        total_acts = sum(activity.values()) or 1
        report += "📊 Активность продавцов:\n"
        for user, count in activity.items():
            percent = round(count / total_acts * 100, 1)
            report += f"– @{user}: {percent}%\n"
        for uname in SELLERS:
            try:
                bot.send_message(f"@{uname}", report, parse_mode="Markdown")
            except Exception:
                pass
        print("✅ Отчёт отправлен продавцам.")

# === ЕЖЕДНЕВНОЕ НАПОМИНАНИЕ ===
def daily_reminder():
    for uname in SELLERS:
        try:
            bot.send_message(f"@{uname}", "📋 Напоминание: добавьте сегодня хотя бы 3 позиции в систему.")
        except Exception:
            pass
    print("🔔 Отправлены ежедневные напоминания.")

# === ПЛАНИРОВЩИК ===
scheduler = BackgroundScheduler(timezone=TIMEZONE)
scheduler.add_job(daily_reminder, 'cron', hour=10)  # каждый день в 10:00
scheduler.add_job(weekly_report, 'cron', day_of_week='tue', hour=21)
scheduler.start()

print("🤖 Бот запущен и работает 24/7...")
bot.infinity_polling()
