import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8999035301


# =====================================================
# WEB SERVER ДЛЯ RENDER
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
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


# =====================================================
# ГЛАВНОЕ МЕНЮ
# =====================================================

def main_menu():
    keyboard = [
        [
            InlineKeyboardButton(
                "🛒 Магазин",
                callback_data="shop",
            ),
            InlineKeyboardButton(
                "🆓 Бесплатный проект",
                callback_data="free",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔨 Собрать проект",
                callback_data="build",
            ),
            InlineKeyboardButton(
                "📁 Мои проекты",
                callback_data="projects",
            ),
        ],
        [
            InlineKeyboardButton(
                "🆘 Поддержка",
                callback_data="support",
            ),
            InlineKeyboardButton(
                "🤝 Партнёрка",
                callback_data="partner",
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
                callback_data="shop_projects",
            ),
        ],
        [
            InlineKeyboardButton(
                "📢 Реклама в канале",
                callback_data="shop_ads",
            ),
        ],
        [
            InlineKeyboardButton(
                "🏠 Главное меню",
                callback_data="main_menu",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =====================================================
# КНОПКИ НАЗАД
# =====================================================

def back_menu(back_callback="main_menu"):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "◀️ Назад",
                callback_data=back_callback,
            ),
        ],
        [
            InlineKeyboardButton(
                "🏠 Главное меню",
                callback_data="main_menu",
            ),
        ],
    ])


# =====================================================
# /START
# =====================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        reply_markup=main_menu(),
    )


# =====================================================
# ОБРАБОТКА КНОПОК
# =====================================================

async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    # -------------------------
    # ГЛАВНОЕ МЕНЮ
    # -------------------------

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
            reply_markup=main_menu(),
        )

    # -------------------------
    # МАГАЗИН
    # -------------------------

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
            reply_markup=shop_menu(),
        )

    # -------------------------
    # ПРОЕКТЫ
    # -------------------------

    elif query.data == "shop_projects":
        text = (
            "📦 ПРОЕКТЫ\n\n"
            "Здесь будут отображаться доступные проекты.\n\n"
            "Пока каталог пуст."
        )

        await query.edit_message_text(
            text,
            reply_markup=back_menu("shop"),
        )

    # -------------------------
    # РЕКЛАМА
    # -------------------------

    elif query.data == "shop_ads":
        text = (
            "📢 РЕКЛАМА В КАНАЛЕ\n\n"
            "Здесь будут тарифы на рекламу.\n\n"
            "Раздел находится в разработке."
        )

        await query.edit_message_text(
            text,
            reply_markup=back_menu("shop"),
        )

    # -------------------------
    # БЕСПЛАТНЫЙ ПРОЕКТ
    # -------------------------

    elif query.data == "free":
        text = (
            "🆓 БЕСПЛАТНЫЙ ПРОЕКТ\n\n"
            "Здесь появится бесплатный проект."
        )

        await query.edit_message_text(
            text,
            reply_markup=back_menu(),
        )

    # -------------------------
    # СОБРАТЬ ПРОЕКТ
    # -------------------------

    elif query.data == "build":
        text = (
            "🔨 СОБРАТЬ ПРОЕКТ\n\n"
            "Здесь бот начнёт задавать вопросы "
            "для сборки проекта."
        )

        await query.edit_message_text(
            text,
            reply_markup=back_menu(),
        )

    # -------------------------
    # МОИ ПРОЕКТЫ
    # -------------------------

    elif query.data == "projects":
        text = (
            "📁 МОИ ПРОЕКТЫ\n\n"
            "У тебя пока нет проектов."
        )

        await query.edit_message_text(
            text,
            reply_markup=back_menu(),
        )

    # -------------------------
    # ПОДДЕРЖКА
    # -------------------------

    elif query.data == "support":
        text = (
            "🆘 ПОДДЕРЖКА\n\n"
            "Здесь будет связь с поддержкой."
        )

        await query.edit_message_text(
            text,
            reply_markup=back_menu(),
        )

    # -------------------------
    # ПАРТНЁРКА
    # -------------------------

    elif query.data == "partner":
        text = (
            "🤝 ПАРТНЁРКА\n\n"
            "Здесь появится партнёрская программа SVOYAK."
        )

        await query.edit_message_text(
            text,
            reply_markup=back_menu(),
        )


# =====================================================
# ЗАПУСК
# =====================================================

def run():
    if not TOKEN:
        raise RuntimeError(
            "Не задана переменная окружения BOT_TOKEN"
        )

    # HTTP-сервер запускаем отдельно,
    # чтобы Render Web Service видел открытый порт.
    threading.Thread(
        target=run_web_server,
        daemon=True,
    ).start()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CallbackQueryHandler(buttons)
    )

    print("SVOYAK BOT запущен!")

    app.run_polling()


if __name__ == "__main__":
    run()
