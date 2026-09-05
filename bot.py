import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN", "ВСТАВЬ_ТОКЕН_СЮДА")


def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("🛒 Магазин", callback_data="shop"),
            InlineKeyboardButton("🆓 Бесплатный проект", callback_data="free"),
        ],
        [
            InlineKeyboardButton("🔨 Собрать проект", callback_data="build"),
            InlineKeyboardButton("📁 Мои проекты", callback_data="projects"),
        ],
        [
            InlineKeyboardButton("🆘 Поддержка", callback_data="support"),
            InlineKeyboardButton("🤝 Партнёрка", callback_data="partner"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def shop_menu():
    keyboard = [
        [
            InlineKeyboardButton("📦 Проекты", callback_data="shop_projects"),
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name or "пользователь"

    text = (
        f"🙂 {name}, привет!\n\n"
        "Собираю готовый мобильный проект Black Russia под твой сервер: "
        "своё название, свои цвета, своя иконка, свой APK.\n\n"
        "💸 От 399 ⭐   🕓 Сборка ~10 минут   ✅ Всё автоматически\n\n"
        "Мод, база данных и приложение устанавливаются на твой сервер "
        "автоматически — тебе нужно только ответить на вопросы бота.\n\n"
        "Выбери раздел в меню под строкой ввода."
    )

    await update.message.reply_text(
        text,
        reply_markup=main_menu(),
    )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "main_menu":
        user = query.from_user
        name = user.first_name or "пользователь"

        text = (
            f"🙂 {name}, привет!\n\n"
            "Собираю готовый мобильный проект Black Russia под твой сервер: "
            "своё название, свои цвета, своя иконка, свой APK.\n\n"
            "💸 От 399 ⭐   🕓 Сборка ~10 минут   ✅ Всё автоматически\n\n"
            "Мод, база данных и приложение устанавливаются на твой сервер "
            "автоматически — тебе нужно только ответить на вопросы бота.\n\n"
            "Выбери раздел в меню под строкой ввода."
        )

        await query.edit_message_text(
            text,
            reply_markup=main_menu(),
        )

    elif query.data == "shop":
        text = (
            "🪙 МАГАЗИН SVOYAK\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "В одном месте: готовые игровые проекты, "
            "реклама в канале и услуги для владельцев ULTRA.\n\n"
            "Выбери нужный раздел ниже. Стоимость в Telegram Stars "
            "считается по единому курсу магазина.\n\n"
            "🪙 Автооплата: Telegram Stars.\n"
            "🔓 После оплаты доступ выдаётся автоматически."
        )

        await query.edit_message_text(
            text,
            reply_markup=shop_menu(),
        )

    elif query.data == "shop_projects":
        await query.edit_message_text(
            "📦 ПРОЕКТЫ\n\n"
            "Здесь будут отображаться доступные проекты.\n\n"
            "Пока каталог пуст.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "◀️ Назад",
                        callback_data="shop",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🏠 Главное меню",
                        callback_data="main_menu",
                    )
                ],
            ]),
        )

    elif query.data == "shop_ads":
        await query.edit_message_text(
            "📢 РЕКЛАМА В КАНАЛЕ\n\n"
            "Здесь будут тарифы на рекламу.\n\n"
            "Раздел находится в разработке.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "◀️ Назад",
                        callback_data="shop",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🏠 Главное меню",
                        callback_data="main_menu",
                    )
                ],
            ]),
        )

    elif query.data == "free":
        await query.edit_message_text(
            "🆓 БЕСПЛАТНЫЙ ПРОЕКТ\n\n"
            "Здесь появится бесплатный проект.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "
