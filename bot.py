import os
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

# ID администратора SVOYAK
ADMIN_ID = 8999035301


# =====================================================
# WEB-СЕРВЕР ДЛЯ RENDER
# =====================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"SVOYAK BOT is running!")

    def log_message(self, format, *args):
        return


def run_web_server():
    port = int(os.getenv("PORT", "10000"))

    server = HTTPServer(
        ("0.0.0.0", port),
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

    return InlineKeyboardMarkup(keyboard)


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

    return InlineKeyboardMarkup(keyboard)


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

    return InlineKeyboardMarkup(keyboard)


# =====================================================
# PRO
# =====================================================

def pro_menu():

    keyboard = [
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
    ]

    return InlineKeyboardMarkup(keyboard)


# =====================================================
# ULTIMATE
# =====================================================

def ultimate_menu():

    keyboard = [
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
    ]

    return InlineKeyboardMarkup(keyboard)


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
        ]
    ])


# =====================================================
# ОБЫЧНОЕ МЕНЮ НАЗАД
# =====================================================

def back_menu(callback="main_menu"):

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

    keyboard = [
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
    ]

    return InlineKeyboardMarkup(keyboard)


async def show_support(query):

    text = (
        "💬 ПОДДЕРЖКА SVOYAK BOT\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "⬆️ По всем вопросам пишите:\n"
        "@svoyak_support_bot\n\n"
        "👛 Если вопрос связан с оплатой, "
        "укажите номер заказа и подробно опишите ситуацию.\n\n"
        "📨 Также обращение можно отправить командой:\n"
        "/paysupport номер заказа и что случилось\n\n"
        "⚠️ Пожалуйста, не отправляйте несколько "
        "одинаковых сообщений подряд."
    )

    await query.edit_message_text(
        text,
        reply_markup=support_menu()
    )


# =====================================================
# START
# =====================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

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
            "• Авторство полностью твоё\n"
            "• Обновления твоей копии при наличии соответствующих прав\n\n"
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
            "Готов к нагрузке\n"
            "• Цель — стабильная работа при высоком онлайне\n"
            "• Код оптимизирован\n"
            "• Основные причины крашей исправляются в процессе сборки\n\n"
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
            "• Установка мода и базы на твой сервер\n"
            "• Бесплатные обновления при наличии соответствующих прав\n\n"
            "Только в ULTIMATE v2.2\n"
            "• Маркетплейс, гаражи, контейнеры\n"
            "• Аукцион, трейд, Black Pass\n"
            "• Блэкджек, кости, водолаз\n"
            "• Тюнинг-центры как бизнесы\n"
            "• Оптимизация под высокий онлайн\n"
            "• Персональная лицензия на твой сервер\n"
            "• Подключение сайта логов и AutoDonate\n\n"
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

        await query.edit_message_text(
            "🔨 СОБРАТЬ ПРОЕКТ\n\n"
            "После покупки здесь можно будет начать "
            "персональную сборку проекта.",
            reply_markup=back_menu()
        )

    # =================================================
    # МОИ ПРОЕКТЫ
    # =================================================

    elif query.data == "projects":

        await query.edit_message_text(
            "📁 МОИ ПРОЕКТЫ\n\n"
            "Здесь будут отображаться купленные проекты "
            "и статус их сборки.",
            reply_markup=back_menu()
        )

    # =================================================
    # ПАРТНЁРКА
    # =================================================

    elif query.data == "partner":

        await query.edit_message_text(
            "🤝 ПАРТНЁРКА\n\n"
            "Партнёрская программа SVOYAK будет "
            "подключена следующим этапом.",
            reply_markup=back_menu()
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
# ОПЛАТА TELEGRAM STARS
# =====================================================

async def send_project_invoice(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    project_name: str,
    stars: int
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
        payload=f"project:{project_name}:{user.id}",
        currency="XTR",
        prices=prices,
    )


# =====================================================
# PRE-CHECKOUT
# =====================================================

async def precheckout_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.pre_checkout_query

    await query.answer(
        ok=True
    )


# =====================================================
# УСПЕШНАЯ ОПЛАТА
# =====================================================

async def successful_payment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    payment = update.message.successful_payment

    user = update.effective_user

    payload = payment.invoice_payload

    if not payload.startswith("project:"):
        return

    parts = payload.split(
        ":",
        2
    )

    if len(parts) != 3:
        return

    project_name = parts[1]

    # -------------------------------------------------
    # СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЮ
    # -------------------------------------------------

    text = (
        "✅ ОПЛАТА ПОЛУЧЕНА!\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 Проект: {project_name}\n"
        f"👤 Telegram ID: {user.id}\n"
        f"🪙 Оплачено: {payment.total_amount} ⭐\n\n"
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
                    "🏠 Главное меню",
                    callback_data="main_menu"
                )
            ],
        ])
    )

    # -------------------------------------------------
    # УВЕДОМЛЕНИЕ АДМИНУ
    # -------------------------------------------------

    if ADMIN_ID:

        try:

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "💰 НОВАЯ ОПЛАТА\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 Пользователь: {user.first_name}\n"
                    f"🆔 Telegram ID: {user.id}\n"
                    f"📦 Проект: {project_name}\n"
                    f"🪙 Сумма: {payment.total_amount} ⭐\n"
                    f"🧾 Charge ID: "
                    f"{payment.telegram_payment_charge_id}"
                )
            )

        except Exception as error:

            print(
                "Не удалось отправить уведомление админу: "
                f"{error}"
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

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            buttons
        )
    )

    app.add_handler(
        PreCheckoutQueryHandler(
            precheckout_callback
        )
    )

    app.add_handler(
        MessageHandler(
            filters.SUCCESSFUL_PAYMENT,
            successful_payment
        )
    )

    print("SVOYAK BOT запущен!")

    app.run_polling()


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    run()
