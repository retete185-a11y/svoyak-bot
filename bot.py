import os
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

# =====================================================
# НАСТРОЙКИ
# =====================================================

TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 8999035301

DATA_FILE = "svoyak_data.json"


# =====================================================
# БАЗА ДАННЫХ JSON
# =====================================================

def load_data():

    if not os.path.exists(DATA_FILE):

        return {
            "users": {}
        }

    try:

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if "users" not in data:
            data["users"] = {}

        return data

    except Exception:

        return {
            "users": {}
        }


def save_data(data):

    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4
        )


def get_user(data, user_id):

    user_id = str(user_id)

    if user_id not in data["users"]:

        data["users"][user_id] = {
            "referrer": None,
            "projects": [],
            "balance": 0,
            "total_profit": 0,
            "monthly_profit": 0,
            "weekly_profit": 0,
            "yesterday_profit": 0,
            "today_profit": 0,
            "referrals": [],
            "has_purchased": False
        }

    return data["users"][user_id]


# =====================================================
# WEB-СЕРВЕР RENDER
# =====================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        self.send_response(200)

        self.end_headers()

        self.wfile.write(
            b"SVOYAK BOT is running!"
        )

    def log_message(
        self,
        format,
        *args
    ):

        return


def run_web_server():

    port = int(
        os.getenv(
            "PORT",
            "10000"
        )
    )

    server = HTTPServer(
        (
            "0.0.0.0",
            port
        ),
        HealthHandler
    )

    server.serve_forever()


# =====================================================
# ГЛАВНОЕ МЕНЮ
# =====================================================

def main_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "🛒 Магазин",
                callback_data="shop"
            ),

            InlineKeyboardButton(
                "🆓 Бесплатный проект",
                callback_data="free"
            ),
        ],

        [
            InlineKeyboardButton(
                "🔨 Собрать проект",
                callback_data="build"
            ),

            InlineKeyboardButton(
                "📁 Мои проекты",
                callback_data="projects"
            ),
        ],

        [
            InlineKeyboardButton(
                "🆘 Поддержка",
                callback_data="support"
            ),

            InlineKeyboardButton(
                "🤝 Партнёрка",
                callback_data="partner"
            ),
        ],

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# =====================================================
# МАГАЗИН
# =====================================================

def shop_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "📦 Проекты",
                callback_data="shop_projects"
            )
        ],

        [
            InlineKeyboardButton(
                "📢 Реклама в канале",
                callback_data="shop_ads"
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 Главное меню",
                callback_data="main_menu"
            )
        ],

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# =====================================================
# ПРОЕКТЫ
# =====================================================

def projects_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "📦 BLACK RUSSIA PRO · ⭐️ 200",
                callback_data="project_pro"
            )
        ],

        [
            InlineKeyboardButton(
                "🎁 BLACK RUSSIA ULTIMATE v2.2 · ⭐️ 500",
                callback_data="project_ultimate"
            )
        ],

        [
            InlineKeyboardButton(
                "👁 PRO ИЛИ ULTIMATE v2.2",
                callback_data="project_compare"
            )
        ],

        [
            InlineKeyboardButton(
                "◀️ Назад",
                callback_data="shop"
            )
        ],

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# =====================================================
# PRO МЕНЮ
# =====================================================

def pro_menu():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🪙 TELEGRAM STARS · 200",
                callback_data="buy_pro"
            )
        ],

        [
            InlineKeyboardButton(
                "◀️ Назад к проектам",
                callback_data="shop_projects"
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 Главное меню",
                callback_data="main_menu"
            )
        ],

    ])


# =====================================================
# ULTIMATE МЕНЮ
# =====================================================

def ultimate_menu():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🪙 TELEGRAM STARS · 500",
                callback_data="buy_ultimate"
            )
        ],

        [
            InlineKeyboardButton(
                "◀️ Назад к проектам",
                callback_data="shop_projects"
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 Главное меню",
                callback_data="main_menu"
            )
        ],

    ])


# =====================================================
# СРАВНЕНИЕ
# =====================================================

def compare_menu():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "◀️ Назад к проектам",
                callback_data="shop_projects"
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 Главное меню",
                callback_data="main_menu"
            )
        ],

    ])


# =====================================================
# НАЗАД
# =====================================================

def back_menu(
    callback="main_menu"
):

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "◀️ Назад",
                callback_data=callback
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 Главное меню",
                callback_data="main_menu"
            )
        ],

    ])


# =====================================================
# ПОДДЕРЖКА
# =====================================================

def support_menu():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "💬 Написать в поддержку",
                url="https://t.me/svoyak_support_bot"
            )
        ],

        [
            InlineKeyboardButton(
                "📄 Пользовательское соглашение",
                url="https://telegra.ph/Polzovatelskoe-soglashenie-SVOYAK-09-05-2"
            )
        ],

        [
            InlineKeyboardButton(
                "🔐 Политика конфиденциальности",
                url="https://telegra.ph/SVOYAK--Politika-konfidencialnosti-09-05"
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 Главное меню",
                callback_data="main_menu"
            )
        ],

    ])


# =====================================================
# ПАРТНЁРСКАЯ ПРОГРАММА
# =====================================================

async def show_partner(
    query,
    context
):

    data = load_data()

    user_id = query.from_user.id

    user = get_user(
        data,
        user_id
    )

    # Получаем username бота автоматически
    bot_info = await context.bot.get_me()

    bot_username = bot_info.username

    referral_link = (
        f"https://t.me/{bot_username}"
        f"?start=ref_{user_id}"
    )

    referrals_count = len(
        user.get(
            "referrals",
            []
        )
    )

    text = (
        "💸 ПАРТНЁРСКАЯ ПРОГРАММА\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Наша партнёрская программа позволяет "
        "зарабатывать без вложений. Приглашай новых "
        "пользователей и получай 15% от суммы их покупок.\n\n"

        "📊 Статистика прибыли:\n"
        f"За всё время: {user.get('total_profit', 0)} 💸\n"
        f"За месяц: {user.get('monthly_profit', 0)} 💸\n"
        f"За неделю: {user.get('weekly_profit', 0)} 💸\n"
        f"За вчера: {user.get('yesterday_profit', 0)} 💸\n"
        f"За сегодня: {user.get('today_profit', 0)} 💸\n\n"

        f"👛 Текущий баланс: {user.get('balance', 0)} 💸\n"
        f"👥 Реферальных пользователей: {referrals_count}\n\n"

        "🔗 Твоя реферальная ссылка:\n"
        f"{referral_link}\n\n"

        "ℹ Начисления пойдут после твоей первой покупки — "
        "это защита от накрутки. Приглашённые уже засчитываются."
    )

    keyboard = InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🛒 Магазин",
                callback_data="shop"
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 Главное меню",
                callback_data="main_menu"
            )
        ],

    ])

    await query.edit_message_text(
        text,
        reply_markup=keyboard
    )


# =====================================================
# МОИ ПРОЕКТЫ
# =====================================================

async def show_projects(query):

    data = load_data()

    user = get_user(
        data,
        query.from_user.id
    )

    projects = user.get(
        "projects",
        []
    )

    if not projects:

        text = (
            "📁 МОИ ПРОЕКТЫ\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "У тебя пока нет созданных проектов.\n\n"
            "Выбери BLACK RUSSIA PRO или "
            "ULTIMATE v2.2 в магазине."
        )

        keyboard = InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "🛒 Магазин",
                    callback_data="shop"
                )
            ],

            [
                InlineKeyboardButton(
                    "🏠 Главное меню",
                    callback_data="main_menu"
                )
            ],

        ])

        await query.edit_message_text(
            text,
            reply_markup=keyboard
        )

        return

    text = (
        "📁 МОИ ПРОЕКТЫ\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Твои проекты:\n\n"
    )

    for index, project in enumerate(
        projects,
        1
    ):

        text += (
            f"📦 {index}. {project}\n"
        )

    text += (
        "\n🔨 Проект можно открыть "
        "после перехода в студию сборки."
    )

    keyboard = InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🔨 Собрать проект",
                callback_data="build"
            )
        ],

        [
            InlineKeyboardButton(
                "🛒 Магазин",
                callback_data="shop"
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 Главное меню",
                callback_data="main_menu"
            )
        ],

    ])

    await query.edit_message_text(
        text,
        reply_markup=keyboard
    )


# =====================================================
# START
# =====================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    data = load_data()

    user = update.effective_user

    current_user = get_user(
        data,
        user.id
    )

    # =================================================
    # РЕФЕРАЛ
    # =================================================

    if context.args:

        argument = context.args[0]

        if argument.startswith("ref_"):

            ref_id_text = argument[4:]

            try:

                ref_id = int(
                    ref_id_text
                )

                # Нельзя пригласить самого себя
                if ref_id != user.id:

                    # Реферер существует
                    if str(ref_id) in data["users"]:

                        # Только если реферер ещё не назначен
                        if current_user.get(
                            "referrer"
                        ) is None:

                            current_user["referrer"] = ref_id

                            ref_user = get_user(
                                data,
                                ref_id
                            )

                            if user.id not in ref_user["referrals"]:

                                ref_user["referrals"].append(
                                    user.id
                                )

                            save_data(data)

            except ValueError:

                pass

    name = user.first_name or "пользователь"

    text = (
        f"🙂 {name}, привет!\n\n"
        "Собираю готовый мобильный проект Black Russia "
        "под твой сервер: своё название, свои цвета, "
        "своя иконка, свой APK.\n\n"
        "💸 От 399 ⭐   🕓 Сборка ~10 минут   "
        "✅ Всё автоматически\n\n"
        "Мод, база данных и приложение устанавливаются "
        "на твой сервер автоматически — тебе нужно только "
        "ответить на вопросы бота.\n\n"
        "Выбери раздел в меню под строкой ввода."
    )

    await update.message.reply_text(
        text,
        reply_markup=main_menu()
    )


# =====================================================
# КНОПКИ
# =====================================================

async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    # =================================================
    # ГЛАВНОЕ МЕНЮ
    # =================================================

    if query.data == "main_menu":

        user = query.from_user

        name = user.first_name or "пользователь"

        text = (
            f"🙂 {name}, привет!\n\n"
            "Собираю готовый мобильный проект Black Russia "
            "под твой сервер: своё название, свои цвета, "
            "своя иконка, свой APK.\n\n"
            "💸 От 399 ⭐   🕓 Сборка ~10 минут   "
            "✅ Всё автоматически\n\n"
            "Мод, база данных и приложение устанавливаются "
            "на твой сервер автоматически — тебе нужно только "
            "ответить на вопросы бота.\n\n"
            "Выбери раздел в меню под строкой ввода."
        )

        await query.edit_message_text(
            text,
            reply_markup=main_menu()
        )

    # =================================================
    # ПОДДЕРЖКА
    # =================================================

    elif query.data == "support":

        await show_support(query)

    # =================================================
    # ПАРТНЁРКА
    # =================================================

    elif query.data == "partner":

        await show_partner(
            query,
            context
        )

    # =================================================
    # МОИ ПРОЕКТЫ
    # =================================================

    elif query.data == "projects":

        await show_projects(
            query
        )

    # =================================================
    # МАГАЗИН
    # =================================================

    elif query.data == "shop":

        text = (
            "🪙 МАГАЗИН SVOYAK\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "В одном месте: готовые игровые проекты, "
            "реклама в канале и услуги для владельцев ULTRA.\n\n"
            "Выбери нужный раздел ниже. Стоимость в Telegram "
            "Stars считается по единому курсу магазина.\n\n"
            "🪙 Автооплата: Telegram Stars.\n"
            "🔓 После оплаты доступ выдаётся автоматически."
        )

        await query.edit_message_text(
            text,
            reply_markup=shop_menu()
        )

    # =================================================
    # ПРОЕКТЫ
    # =================================================

    elif query.data == "shop_projects":

        text = (
            "📦 ПРОЕКТЫ BLACK RUSSIA\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "В магазине два готовых проекта. После оплаты "
            "заказ закрепляется за твоим Telegram и открывает "
            "персональную сборку.\n\n"
            "📦 BLACK RUSSIA PRO · ⭐️ 200\n"
            "Доработанный проект с упором на тюнинг, "
            "визуал и быстрый запуск.\n\n"
            "🎁 BLACK RUSSIA ULTIMATE v2.2 · ⭐️ 500\n"
            "Расширенная версия PRO с дополнительными системами.\n\n"
            "🪙 Автооплата: Telegram Stars.\n"
            "🔓 После оплаты доступ выдаётся автоматически."
        )

        await query.edit_message_text(
            text,
            reply_markup=projects_menu()
        )

    # =================================================
    # PRO
    # =================================================

    elif query.data == "project_pro":

        text = (
            "📦 BLACK RUSSIA PRO\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "⭐️ 200   🕓 сборка ~10 минут\n\n"
            "Готовый мод с упором на тюнинг и визуал. "
            "Ставится на твой сервер целиком: мод, база данных "
            "и приложение.\n\n"
            "Что внутри\n"
            "• Стайлинг, тех-центр и шиномонтаж — тюнинг сохраняется\n"
            "• Радиальное меню, GPS-метки и зелёные зоны\n"
            "• Кейсы, ревард-система, автосалоны с выбором цвета\n"
            "• Донат и инвентарь работают полностью\n\n"
            "Проект остаётся твоим\n"
            "• Название, цвета, иконка и ID приложения — под тебя\n"
            "• APK не конфликтует с другими проектами\n"
            "• Авторство полностью твоё\n\n"
            "🔓 Доступ откроется сразу после оплаты."
        )

        await query.edit_message_text(
            text,
            reply_markup=pro_menu()
        )

    # =================================================
    # ULTIMATE
    # =================================================

    elif query.data == "project_ultimate":

        text = (
            "📦 BLACK RUSSIA ULTIMATE v2.2\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "⭐️ 500   🕓 сборка ~10 минут\n\n"
            "Всё из BLACK RUSSIA PRO плюс дополнительные системы.\n\n"
            "Что добавлено\n"
            "• Маркетплейс, гаражи и контейнеры\n"
            "• Аукцион, система трейда и Black Pass\n"
            "• Блэкджек, кости и система водолаза\n"
            "• Тюнинг-центры работают как полноценные бизнесы\n\n"
            "Проект остаётся твоим\n"
            "• Название, цвета, логотипы, иконка и ID приложения — под тебя\n"
            "• Персональная лицензия привязывается к твоему серверу\n"
            "• Авторство полностью твоё\n\n"
            "🔓 Доступ откроется сразу после оплаты."
        )

        await query.edit_message_text(
            text,
            reply_markup=ultimate_menu()
        )

    # =================================================
    # СРАВНЕНИЕ
    # =================================================

    elif query.data == "project_compare":

        text = (
            "👁 PRO ИЛИ ULTIMATE v2.2\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "📦 BLACK RUSSIA PRO · 200 🌟\n"
            "📦 BLACK RUSSIA ULTIMATE · 500 🌟\n\n"
            "Одинаково в обоих\n"
            "• Свой APK: название, цвета, иконка, ID приложения\n"
            "• Тюнинг-центры, радиальное меню, зелёные зоны, кейсы\n"
            "• Донат и инвентарь\n"
            "• Установка мода и базы на твой сервер\n\n"
            "Только в ULTIMATE v2.2\n"
            "• Маркетплейс, гаражи, контейнеры\n"
            "• Аукцион, трейд, Black Pass\n"
            "• Блэкджек, кости, водолаз\n"
            "• Тюнинг-центры как бизнесы\n"
            "• Оптимизация под высокий онлайн\n\n"
            "ℹ Начинаешь и хочешь просто запуститься — бери PRO.\n"
            "Планируешь большой проект с экономикой — ULTIMATE v2.2."
        )

        await query.edit_message_text(
            text,
            reply_markup=compare_menu()
        )

    # =================================================
    # БЕСПЛАТНЫЙ ПРОЕКТ
    # =================================================

    elif query.data == "free":

        await query.edit_message_text(
            "🆓 БЕСПЛАТНЫЙ ПРОЕКТ\n\n"
            "Здесь появится бесплатный проект.",
            reply_markup=back_menu()
        )

    # =================================================
    # СОБРАТЬ ПРОЕКТ
    # =================================================

    elif query.data == "build":

        text = (
            "🔨 СБОРКА ПРОЕКТА\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Оплаченных запусков пока нет.\n\n"
            "Купи BLACK RUSSIA PRO или ULTIMATE v2.2 — "
            "и студия откроется сразу после оплаты. "
            "Бесплатная сборка доступна кнопкой "
            "«Бесплатный проект» в меню."
        )

        keyboard = InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "🛒 Купить проект",
                    callback_data="shop"
                )
            ],

            [
                InlineKeyboardButton(
                    "🏠 Главное меню",
                    callback_data="main_menu"
                )
            ],

        ])

        await query.edit_message_text(
            text,
            reply_markup=keyboard
        )

    # =================================================
    # ПАРТНЁРКА
    # =================================================

    elif query.data == "partner":

        await show_partner(
            query,
            context
        )

    # =================================================
    # РЕКЛАМА
    # =================================================

    elif query.data == "shop_ads":

        await query.edit_message_text(
            "📢 РЕКЛАМА В КАНАЛЕ\n\n"
            "Здесь будут тарифы на рекламу.",
            reply_markup=back_menu("shop")
        )

    # =================================================
    # ПОКУПКА PRO
    # =================================================

    elif query.data == "buy_pro":

        await send_project_invoice(
            update,
            context,
            "BLACK RUSSIA PRO",
            200
        )

    # =================================================
    # ПОКУПКА ULTIMATE
    # =================================================

    elif query.data == "buy_ultimate":

        await send_project_invoice(
            update,
            context,
            "BLACK RUSSIA ULTIMATE v2.2",
            500
        )


# =====================================================
# СЧЁТ НА ОПЛАТУ
# =====================================================

async def send_project_invoice(
    update,
    context,
    project_name,
    stars
):

    user = update.effective_user

    prices = [
        LabeledPrice(
            label=project_name,
            amount=stars
        )
    ]

    await context.bot.send_invoice(
        chat_id=user.id,
        title=project_name,
        description=(
            f"Персональная сборка проекта "
            f"{project_name} под твой сервер."
        ),
        payload=(
            f"project:{project_name}:{user.id}"
        ),
        currency="XTR",
        prices=prices
    )


# =====================================================
# PRE-CHECKOUT
# =====================================================

async def precheckout_callback(
    update,
    context
):

    query = update.pre_checkout_query

    await query.answer(
        ok=True
    )


# =====================================================
# УСПЕШНАЯ ОПЛАТА
# =====================================================

async def successful_payment(
    update,
    context
):

    payment = (
        update.message.successful_payment
    )

    user = update.effective_user

    payload = payment.invoice_payload

    if not payload.startswith(
        "project:"
    ):

        return

    parts = payload.split(
        ":",
        2
    )

    if len(parts) != 3:

        return

    project_name = parts[1]

    stars = payment.total_amount

    # =================================================
    # ЗАГРУЖАЕМ ДАННЫЕ
    # =================================================

    data = load_data()

    buyer = get_user(
        data,
        user.id
    )

    # =================================================
    # ДОБАВЛЯЕМ ПРОЕКТ
    # =================================================

    if project_name not in buyer["projects"]:

        buyer["projects"].append(
            project_name
        )

    # Пользователь совершил покупку
    buyer["has_purchased"] = True

    # =================================================
    # РЕФЕРАЛЬНОЕ НАЧИСЛЕНИЕ
    # =================================================

    referrer_id = buyer.get(
        "referrer"
    )

    referral_profit = 0

    if referrer_id:

        referrer = get_user(
            data,
            referrer_id
        )

        # Начисления только если реферер
        # уже совершил собственную покупку
        if referrer.get(
            "has_purchased",
            False
        ):

            referral_profit = int(
                stars * 0.15
            )

            referrer["balance"] += (
                referral_profit
            )

            referrer["total_profit"] += (
                referral_profit
            )

            referrer["monthly_profit"] += (
                referral_profit
            )

            referrer["weekly_profit"] += (
                referral_profit
            )

            referrer["today_profit"] += (
                referral_profit
            )

    # =================================================
    # СОХРАНЯЕМ
    # =================================================

    save_data(
        data
    )

    # =================================================
    # ПОЛЬЗОВАТЕЛЮ
    # =================================================

    text = (
        "✅ ОПЛАТА ПОЛУЧЕНА!\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 Проект: {project_name}\n"
        f"👤 Telegram ID: {user.id}\n"
        f"🪙 Оплачено: {stars} ⭐\n\n"
        "📁 Проект добавлен в «Мои проекты».\n"
        "🔓 Заказ закреплён за твоим Telegram.\n"
        "🔨 Персональная сборка подготовлена к запуску.\n\n"
        "⏳ Следующий этап — настройка названия, "
        "цветов, иконки и параметров сервера."
    )

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "📁 Мои проекты",
                    callback_data="projects"
                )
            ],

            [
                InlineKeyboardButton(
                    "🔨 Собрать проект",
                    callback_data="build"
                )
            ],

            [
                InlineKeyboardButton(
                    "🏠 Главное меню",
                    callback_data="main_menu"
                )
            ],

        ])
    )

    # =================================================
    # УВЕДОМЛЕНИЕ АДМИНУ
    # =================================================

    if ADMIN_ID:

        try:

            admin_text = (
                "💰 НОВАЯ ОПЛАТА\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 Пользователь: {user.first_name}\n"
                f"🆔 Telegram ID: {user.id}\n"
                f"📦 Проект: {project_name}\n"
                f"🪙 Сумма: {stars} ⭐"
            )

            if referral_profit > 0:

                admin_text += (
                    f"\n💸 Реферальное начисление: "
                    f"{referral_profit} 💸"
                )

            admin_text += (
                f"\n🧾 Charge ID: "
                f"{payment.telegram_payment_charge_id}"
            )

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_text
            )

        except Exception as error:

            print(
                "Ошибка уведомления админу:",
                error
            )


# =====================================================
# ЗАПУСК
# =====================================================

def run():

    if not TOKEN:

        raise RuntimeError(
            "Не задан BOT_TOKEN в Environment Variables Render."
        )

    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

    # /start
    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    # Inline-кнопки
    app.add_handler(
        CallbackQueryHandler(
            buttons
        )
    )

    # Pre-checkout
    app.add_handler(
        PreCheckoutQueryHandler(
            precheckout_callback
        )
    )

    # Успешная оплата
    app.add_handler(
        MessageHandler(
            filters.SUCCESSFUL_PAYMENT,
            successful_payment
        )
    )

    print(
        "SVOYAK BOT запущен!"
    )

    app.run_polling()


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    run()
