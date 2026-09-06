import os
import json
import threading
import shutil
import zipfile
import subprocess
import time
import asyncio
from pathlib import Path
from ftplib import FTP
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

BASE_DIR = Path("svoyak_builds")
ADMIN_FILES_DIR = Path("admin_files")

MOD_FILE = ADMIN_FILES_DIR / "clean_mod.zip"
SQL_FILE = ADMIN_FILES_DIR / "svoyak.sql"

# JNI-проект
JNI_FILE = ADMIN_FILES_DIR / "jni_project.zip"
JNI_DIR = ADMIN_FILES_DIR / "jni_project"

# Скрипт сборки JNI
BUILD_SCRIPT = Path(__file__).resolve().parent / "build_client.sh"

BASE_DIR.mkdir(parents=True, exist_ok=True)
ADMIN_FILES_DIR.mkdir(parents=True, exist_ok=True)


# =====================================================
# JSON
# =====================================================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "users": {},
            "builds": {}
        }

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if "users" not in data:
            data["users"] = {}

        if "builds" not in data:
            data["builds"] = {}

        return data

    except Exception as error:
        print("Ошибка чтения JSON:", error)

        return {
            "users": {},
            "builds": {}
        }


def save_data(data):
    temp_file = DATA_FILE + ".tmp"

    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4
        )

    os.replace(temp_file, DATA_FILE)


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
            "has_purchased": False,
            "free_build": None
        }

    user = data["users"][user_id]

    if "free_build" not in user:
        user["free_build"] = None

    return user


# =====================================================
# WEB SERVER
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
    return InlineKeyboardMarkup([
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
    ])


# =====================================================
# НАЗАД
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
# SHOP
# =====================================================

def shop_menu():
    return InlineKeyboardMarkup([
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
    ])


def projects_menu():
    return InlineKeyboardMarkup([
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
    ])


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
# SUPPORT
# =====================================================

async def show_support(query):

    text = (
        "🆘 ПОДДЕРЖКА\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Если у тебя возник вопрос по проекту, "
        "сборке или работе SVOYAK — обратись в поддержку."
    )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
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
    )


# =====================================================
# PARTNER
# =====================================================

async def show_partner(query, context):

    data = load_data()

    user_id = query.from_user.id

    user = get_user(
        data,
        user_id
    )

    bot_info = await context.bot.get_me()

    referral_link = (
        f"https://t.me/{bot_info.username}"
        f"?start=ref_{user_id}"
    )

    referrals_count = len(
        user.get("referrals", [])
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

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
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
    )


# =====================================================
# MY PROJECTS
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

        await query.edit_message_text(
            "📁 МОИ ПРОЕКТЫ\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "У тебя пока нет созданных проектов.\n\n"
            "Выбери BLACK RUSSIA PRO или ULTIMATE v2.2 в магазине.",
            reply_markup=InlineKeyboardMarkup([
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
        )

        return

    text = (
        "📁 МОИ ПРОЕКТЫ\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Твои проекты:\n\n"
    )

    for index, project in enumerate(projects, 1):
        text += f"📦 {index}. {project}\n"

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
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
    )


# =====================================================
# FREE BUILD
# =====================================================

def free_build_start():
    return (
        "🛠 Новая сборка проекта\n\n"
        "Я настрою клиентскую библиотеку, подготовлю "
        "чистый мод и при необходимости загружу его на FTP.\n\n"
        "Шаг 1 из 7 — игровой сервер\n"
        "Отправь IP и порт в формате:\n"
        "80.242.59.112:6793"
    )


async def start_free_build(query):

    data = load_data()

    user = get_user(
        data,
        query.from_user.id
    )

    user["free_build"] = {
        "step": 1,
        "server": None,
        "project_name": None,
        "bonuses": None,
        "links": None,
        "owner": None,
        "mysql": None,
        "ftp": None,
        "status": "collecting"
    }

    save_data(data)

    await query.edit_message_text(
        free_build_start(),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🏠 Главное меню",
                    callback_data="main_menu"
                )
            ]
        ])
    )


def valid_server(value):

    if ":" not in value:
        return None

    ip, port = value.rsplit(":", 1)

    ip = ip.strip()
    port = port.strip()

    if not ip:
        return None

    try:
        port_number = int(port)
    except ValueError:
        return None

    if port_number < 1 or port_number > 65535:
        return None

    return {
        "ip": ip,
        "port": port_number,
        "address": f"{ip}:{port_number}"
    }


def parse_bonuses(value):

    parts = value.split()

    if len(parts) != 4:
        return None

    try:
        numbers = [
            int(item)
            for item in parts
        ]
    except ValueError:
        return None

    if any(number < 0 for number in numbers):
        return None

    return {
        "donate": numbers[0],
        "money": numbers[1],
        "vip": numbers[2],
        "level": numbers[3]
    }


def parse_links(value):

    parts = value.split()

    if len(parts) != 3:
        return None

    return {
        "telegram": parts[0],
        "vk": parts[1],
        "website": parts[2]
    }


# =====================================================
# MYSQL
# =====================================================

def parse_mysql(value):

    parts = value.split()

    if len(parts) < 4:
        return None

    host = parts[0]
    username = parts[1]
    database = parts[-1]

    password_parts = parts[2:-1]

    password = " ".join(password_parts)

    if not host:
        return None

    if not username:
        return None

    if not database:
        return None

    if not password:
        return None

    return {
        "host": host,
        "username": username,
        "password": password,
        "database": database
    }


# =====================================================
# FTP PARSE
# =====================================================

def parse_ftp(value):

    parts = value.split()

    if len(parts) != 3:
        return None

    address = parts[0]
    login = parts[1]
    password = parts[2]

    if ":" not in address:
        return None

    ip, port = address.rsplit(":", 1)

    try:
        port = int(port)
    except ValueError:
        return None

    if not ip:
        return None

    if not login:
        return None

    if not password:
        return None

    if port < 1 or port > 65535:
        return None

    return {
        "ip": ip,
        "port": port,
        "login": login,
        "password": password
    }


# =====================================================
# FREE BUILD MESSAGE
# =====================================================

async def free_build_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    if not update.message.text:
        return

    data = load_data()

    user_id = update.effective_user.id

    user = get_user(
        data,
        user_id
    )

    build = user.get("free_build")

    if not build:
        return

    if build.get("status") != "collecting":
        return

    step = build.get("step", 1)

    value = update.message.text.strip()

    # =================================================
    # STEP 1
    # =================================================

    if step == 1:

        server = valid_server(value)

        if not server:

            await update.message.reply_text(
                "❌ Неверный формат.\n\n"
                "Отправь IP и порт так:\n"
                "80.242.59.112:6793"
            )

            return

        build["server"] = server
        build["step"] = 2

        save_data(data)

        await update.message.reply_text(
            "Адрес сервера сохранён.\n\n"
            "Шаг 2 из 7 — название проекта\n"
            "Оно будет указано одновременно в клиентском "
            "hooks.cpp и параметре nameserver чистого мода.\n"
            "Пример: TEST SVOYAK"
        )

        return

    # =================================================
    # STEP 2
    # =================================================

    if step == 2:

        if not value:

            await update.message.reply_text(
                "❌ Название проекта не может быть пустым."
            )

            return

        build["project_name"] = value
        build["step"] = 3

        save_data(data)

        await update.message.reply_text(
            "Название проекта сохранено.\n\n"
            "Шаг 3 из 7 — стартовые бонусы\n"
            "Отправь четыре числа одной строкой:\n"
            "донат деньги VIP уровень\n\n"
            "Пример:\n"
            "10000 80000000 1 1"
        )

        return

    # =================================================
    # STEP 3
    # =================================================

    if step == 3:

        bonuses = parse_bonuses(value)

        if not bonuses:

            await update.message.reply_text(
                "❌ Нужно отправить ровно четыре числа.\n\n"
                "Пример:\n"
                "10000 80000000 1 1"
            )

            return

        build["bonuses"] = bonuses
        build["step"] = 4

        save_data(data)

        await update.message.reply_text(
            "Стартовые бонусы сохранены.\n\n"
            "Шаг 4 из 7 — ссылки проекта\n"
            "Отправь Telegram, VK и сайт через пробел:\n"
            "t.me/myproject vk.com/myproject myproject.ru\n\n"
            "Если какой-то ссылки нет, укажи вместо неё -."
        )

        return

    # =================================================
    # STEP 4
    # =================================================

    if step == 4:

        links = parse_links(value)

        if not links:

            await update.message.reply_text(
                "❌ Нужно указать три значения через пробел.\n\n"
                "Пример:\n"
                "t.me/myproject vk.com/myproject myproject.ru\n\n"
                "Если ссылки нет — используй -."
            )

            return

        build["links"] = links
        build["step"] = 5

        save_data(data)

        await update.message.reply_text(
            "Ссылки проекта сохранены.\n\n"
            "Шаг 5 из 7 — владелец проекта\n"
            "Отправь точный игровой ник владельца.\n"
            "Пример: Test_Svoyak\n\n"
            "👑 Этот ник получит доступ к скрытым FULL-командам "
            "и 13-й уровень администратора после импорта svoyak.sql."
        )

        return

    # =================================================
    # STEP 5
    # =================================================

    if step == 5:

        if not value:

            await update.message.reply_text(
                "❌ Ник владельца не может быть пустым."
            )

            return

        build["owner"] = value
        build["step"] = 6

        save_data(data)

        await update.message.reply_text(
            "Ник владельца сохранён.\n\n"
            "Шаг 6 из 7 — база данных MySQL\n"
            "Отправь четыре значения одной строкой:\n"
            "host username password database\n\n"
            "Пример:\n"
            "127.0.0.1 game_user strong_password game_db\n\n"
            "Бот к базе не подключается: готовый SQL нужно "
            "импортировать вручную.\n\n"
            "Если в пароле есть пробелы — отправь как есть, "
            "имя базы должно быть последним.\n"
            "🔐 Сообщение с паролем бот удалит сразу после чтения."
        )

        return

    # =================================================
    # STEP 6
    # =================================================

    if step == 6:

        mysql = parse_mysql(value)

        if not mysql:

            await update.message.reply_text(
                "❌ Не удалось разобрать настройки MySQL.\n\n"
                "Формат:\n"
                "host username password database\n\n"
                "Пароль может содержать пробелы.\n"
                "Название базы должно быть последним."
            )

            return

        build["mysql"] = mysql
        build["step"] = 7

        save_data(data)

        try:
            await update.message.delete()
        except Exception as error:
            print(
                "Не удалось удалить MySQL сообщение:",
                error
            )

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "• Настройки MySQL приняты, сообщение с паролем удалено.\n\n"
                "Бот не подключается к базе и не импортирует её автоматически. "
                "Готовый svoyak.sql получишь после сборки.\n\n"
                "Шаг 7 из 7 — загрузка мода\n"
                "Отправь доступ к FTP одной строкой:\n"
                "IP:PORT login password\n"
                "Пример: 185.10.20.30:21 mylogin mypassword\n\n"
                "⚠️ Бот удалит только те файлы и папки в корне FTP, "
                "которые совпадают по названию с элементами твоего мода.\n"
                "Другие папки и файлы FTP НЕ будут удалены.\n\n"
                "📦 Мод будет загружен на FTP.\n"
                "🗄 svoyak.sql на FTP загружаться НЕ будет.\n\n"
                "После сборки импортируй svoyak.sql в базу вручную.\n\n"
                "🔐 Сообщение с доступом будет удалено.\n\n"
                "Если загрузка не нужна, отправь пропустить."
            )
        )

        return

    # =================================================
    # STEP 7
    # =================================================

    if step == 7:

        if value.lower() == "пропустить":

            build["ftp"] = None
            build["step"] = 8
            build["status"] = "waiting_build"

            save_data(data)

            await update.message.reply_text(
                "FTP-загрузка отключена.\n\n"
                "⏳ Все настройки получены.\n"
                "Добавляю проект в очередь сборки..."
            )

            await create_build(
                update,
                context,
                data,
                user
            )

            return

        ftp = parse_ftp(value)

        if not ftp:

            await update.message.reply_text(
                "❌ Неверный формат FTP.\n\n"
                "Нужно:\n"
                "IP:PORT login password\n\n"
                "Пример:\n"
                "185.10.20.30:21 mylogin mypassword\n\n"
                "Или отправь:\n"
                "пропустить"
            )

            return

        build["ftp"] = ftp
        build["step"] = 8
        build["status"] = "waiting_build"

        save_data(data)

        try:
            await update.message.delete()
        except Exception as error:
            print(
                "Не удалось удалить FTP сообщение:",
                error
            )

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🔐 Сообщение с доступом к FTP удалено.\n\n"
                "⏳ Все настройки получены.\n"
                "Добавляю проект в очередь сборки..."
            )
        )

        await create_build(
            update,
            context,
            data,
            user
        )


# =====================================================
# REPLACEMENTS
# =====================================================

def replace_in_file(
    file_path,
    replacements
):

    try:
        text = file_path.read_text(
            encoding="utf-8"
        )
    except Exception:
        return False

    changed = False

    for old, new in replacements.items():

        if old in text:

            text = text.replace(
                old,
                str(new)
            )

            changed = True

    if changed:

        file_path.write_text(
            text,
            encoding="utf-8"
        )

    return changed


# =====================================================
# PREPARE MOD
# =====================================================

def prepare_mod(
    build,
    build_dir
):

    mod_dir = build_dir / "mod"

    if mod_dir.exists():
        shutil.rmtree(mod_dir)

    mod_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    if not MOD_FILE.exists():

        return {
            "ok": False,
            "error": (
                "Администратор ещё не загрузил clean_mod.zip "
                "в админ-панель."
            )
        }

    try:

        with zipfile.ZipFile(
            MOD_FILE,
            "r"
        ) as archive:

            bad_file = archive.testzip()

            if bad_file:

                return {
                    "ok": False,
                    "error": (
                        f"ZIP-архив повреждён. "
                        f"Проблемный файл: {bad_file}"
                    )
                }

            root = mod_dir.resolve()

            for member in archive.infolist():

                target = (
                    mod_dir / member.filename
                ).resolve()

                if (
                    target != root
                    and not str(target).startswith(
                        str(root) + os.sep
                    )
                ):

                    return {
                        "ok": False,
                        "error": (
                            "clean_mod.zip содержит "
                            "опасный путь."
                        )
                    }

            archive.extractall(
                mod_dir
            )

    except zipfile.BadZipFile:

        return {
            "ok": False,
            "error": (
                "clean_mod.zip повреждён "
                "или не является ZIP-архивом."
            )
        }

    except Exception as error:

        return {
            "ok": False,
            "error": f"Ошибка распаковки clean_mod.zip: {error}"
        }

    # =================================================
    # MYSQL + ДАННЫЕ ПРОЕКТА
    # =================================================

    mysql = build["mysql"]

    replacements = {

        "YOUR_PROJECT_NAME": build["project_name"],
        "{{PROJECT_NAME}}": build["project_name"],

        "YOUR_DB_HOST": mysql["host"],
        "{{DB_HOST}}": mysql["host"],

        "YOUR_DB_USER": mysql["username"],
        "{{DB_USER}}": mysql["username"],

        "YOUR_DB_PASSWORD": mysql["password"],
        "{{DB_PASSWORD}}": mysql["password"],

        "YOUR_DB_NAME": mysql["database"],
        "{{DB_NAME}}": mysql["database"],

        "YOUR_OWNER_NICK": build["owner"],
        "{{OWNER_NICK}}": build["owner"],

        "YOUR_SERVER_IP": build["server"]["ip"],
        "{{SERVER_IP}}": build["server"]["ip"],

        "YOUR_SERVER_PORT": build["server"]["port"],
        "{{SERVER_PORT}}": build["server"]["port"],

        "YOUR_TELEGRAM": build["links"]["telegram"],
        "{{TELEGRAM}}": build["links"]["telegram"],

        "YOUR_VK": build["links"]["vk"],
        "{{VK}}": build["links"]["vk"],

        "YOUR_WEBSITE": build["links"]["website"],
        "{{WEBSITE}}": build["links"]["website"],

        "YOUR_DONATE": build["bonuses"]["donate"],
        "{{DONATE}}": build["bonuses"]["donate"],

        "YOUR_MONEY": build["bonuses"]["money"],
        "{{MONEY}}": build["bonuses"]["money"],

        "YOUR_VIP": build["bonuses"]["vip"],
        "{{VIP}}": build["bonuses"]["vip"],

        "YOUR_LEVEL": build["bonuses"]["level"],
        "{{LEVEL}}": build["bonuses"]["level"],

        "TEST SVOYAK": build["project_name"],
    }

    text_extensions = (
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".inc",
        ".pwn",
        ".cfg",
        ".ini",
        ".json",
        ".txt",
        ".sql",
        ".xml",
        ".gradle",
        ".properties",
        ".mk",
        ".cmake",
        ".java",
        ".kt",
        ".js",
    )

    for file_path in mod_dir.rglob("*"):

        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in text_extensions:
            continue

        try:
            replace_in_file(
                file_path,
                replacements
            )
        except Exception as error:
            print(
                "Ошибка замены:",
                file_path,
                error
            )

    # =================================================
    # SQL
    # =================================================

    sql_path = generate_sql(
        build,
        build_dir
    )

    if not sql_path:

        return {
            "ok": False,
            "error": "Не удалось подготовить svoyak.sql."
        }

    # SQL остаётся в локальной сборке,
    # но НЕ должен загружаться на FTP.
    #
    # В мод также добавляем SQL, чтобы при необходимости
    # он присутствовал в архиве локальной сборки.
    try:

        shutil.copy2(
            sql_path,
            mod_dir / "svoyak.sql"
        )

    except Exception as error:

        return {
            "ok": False,
            "error": f"Не удалось добавить svoyak.sql в мод: {error}"
        }

    return {
        "ok": True,
        "mod_dir": mod_dir
    }


# =====================================================
# SQL
# =====================================================

def generate_sql(
    build,
    build_dir
):

    if not SQL_FILE.exists():

        print("svoyak.sql отсутствует")

        return None

    output = build_dir / "svoyak.sql"

    try:

        shutil.copy2(
            SQL_FILE,
            output
        )

    except Exception as error:

        print(
            "Ошибка копирования SQL:",
            error
        )

        return None

    replacements = {

        "YOUR_DB_HOST": build["mysql"]["host"],
        "{{DB_HOST}}": build["mysql"]["host"],

        "YOUR_DB_USER": build["mysql"]["username"],
        "{{DB_USER}}": build["mysql"]["username"],

        "YOUR_DB_PASSWORD": build["mysql"]["password"],
        "{{DB_PASSWORD}}": build["mysql"]["password"],

        "YOUR_DB_NAME": build["mysql"]["database"],
        "{{DB_NAME}}": build["mysql"]["database"],

        "YOUR_OWNER_NICK": build["owner"],
        "{{OWNER_NICK}}": build["owner"],

        "YOUR_PROJECT_NAME": build["project_name"],
        "{{PROJECT_NAME}}": build["project_name"],

        "YOUR_SERVER_IP": build["server"]["ip"],
        "{{SERVER_IP}}": build["server"]["ip"],

        "YOUR_SERVER_PORT": build["server"]["port"],
        "{{SERVER_PORT}}": build["server"]["port"],

        "YOUR_DONATE": build["bonuses"]["donate"],
        "{{DONATE}}": build["bonuses"]["donate"],

        "YOUR_MONEY": build["bonuses"]["money"],
        "{{MONEY}}": build["bonuses"]["money"],

        "YOUR_VIP": build["bonuses"]["vip"],
        "{{VIP}}": build["bonuses"]["vip"],

        "YOUR_LEVEL": build["bonuses"]["level"],
        "{{LEVEL}}": build["bonuses"]["level"],
    }

    replace_in_file(
        output,
        replacements
    )

    return output


# =====================================================
# JNI PROJECT
# =====================================================

def prepare_jni_project():

    if not JNI_FILE.exists():

        return {
            "ok": False,
            "error": (
                "JNI-проект не загружен. "
                "Администратор должен загрузить "
                "jni_project.zip через /admin."
            )
        }

    if JNI_DIR.exists():

        try:
            shutil.rmtree(JNI_DIR)

        except Exception as error:

            return {
                "ok": False,
                "error": (
                    f"Не удалось очистить старый JNI-проект: "
                    f"{error}"
                )
            }

    JNI_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    try:

        with zipfile.ZipFile(
            JNI_FILE,
            "r"
        ) as archive:

            bad_file = archive.testzip()

            if bad_file:

                return {
                    "ok": False,
                    "error": (
                        f"JNI ZIP повреждён. "
                        f"Проблемный файл: {bad_file}"
                    )
                }

            root = JNI_DIR.resolve()

            for member in archive.infolist():

                target = (
                    JNI_DIR / member.filename
                ).resolve()

                if (
                    target != root
                    and not str(target).startswith(
                        str(root) + os.sep
                    )
                ):

                    return {
                        "ok": False,
                        "error": (
                            "JNI ZIP содержит опасный путь."
                        )
                    }

            archive.extractall(
                JNI_DIR
            )

    except zipfile.BadZipFile:

        return {
            "ok": False,
            "error": (
                "jni_project.zip повреждён "
                "или не является ZIP-архивом."
            )
        }

    except Exception as error:

        return {
            "ok": False,
            "error": (
                f"Ошибка распаковки JNI-проекта: {error}"
            )
        }

    current_dir = JNI_DIR

    try:

        items = list(
            JNI_DIR.iterdir()
        )

        directories = [
            item
            for item in items
            if item.is_dir()
        ]

        files = [
            item
            for item in items
            if item.is_file()
        ]

        if (
            len(directories) == 1
            and not files
        ):

            current_dir = directories[0]

    except Exception:
        pass

    return {
        "ok": True,
        "dir": current_dir
    }


# =====================================================
# CLIENT / JNI BUILD
# =====================================================

def build_client(
    build,
    build_dir
):

    output = build_dir / "libsvoyak.so"

    jni_result = prepare_jni_project()

    if not jni_result.get("ok"):

        print(
            "JNI ERROR:",
            jni_result.get("error")
        )

        return None

    jni_dir = Path(
        jni_result["dir"]
    )

    if not BUILD_SCRIPT.exists():

        print(
            "BUILD SCRIPT NOT FOUND:",
            BUILD_SCRIPT
        )

        return None

    env = os.environ.copy()

    env["SERVER_IP"] = str(
        build["server"]["ip"]
    )

    env["SERVER_PORT"] = str(
        build["server"]["port"]
    )

    env["SERVER_ADDRESS"] = str(
        build["server"]["address"]
    )

    env["PROJECT_NAME"] = str(
        build["project_name"]
    )

    env["OWNER_NICK"] = str(
        build["owner"]
    )

    env["ANDROID_ABI"] = "arm64-v8a"

    env["ANDROID_NDK_VERSION"] = "r25c"

    env["SVOYAK_BUILD_DIR"] = str(
        build_dir.resolve()
    )

    try:

        print(
            "================================================="
        )

        print(
            "SVOYAK JNI BUILD"
        )

        print(
            "JNI DIR:",
            jni_dir
        )

        print(
            "SERVER:",
            build["server"]["address"]
        )

        print(
            "PROJECT:",
            build["project_name"]
        )

        print(
            "OWNER:",
            build["owner"]
        )

        print(
            "ABI: arm64-v8a"
        )

        print(
            "NDK: r25c"
        )

        print(
            "================================================="
        )

        result = subprocess.run(
            [
                "bash",
                str(BUILD_SCRIPT.resolve())
            ],
            cwd=str(jni_dir),
            capture_output=True,
            text=True,
            timeout=900,
            env=env
        )

        print(
            "BUILD RETURN CODE:",
            result.returncode
        )

        if result.stdout:

            print(
                "BUILD STDOUT:"
            )

            print(
                result.stdout[-10000:]
            )

        if result.stderr:

            print(
                "BUILD STDERR:"
            )

            print(
                result.stderr[-10000:]
            )

        if result.returncode != 0:
            return None

        candidates = [

            jni_dir / "libsvoyak.so",

            jni_dir / "build" / "libsvoyak.so",

            jni_dir / "output" / "libsvoyak.so",

            jni_dir / "libs" / "libsvoyak.so",

            jni_dir / "app" / "build" / "intermediates"
            / "cxx" / "Release" / "arm64-v8a"
            / "obj" / "arm64-v8a"
            / "libsvoyak.so",

            jni_dir / "app" / "build" / "intermediates"
            / "cxx" / "Release"
            / "obj" / "arm64-v8a"
            / "libsvoyak.so",

            jni_dir / "app" / "build" / "intermediates"
            / "cxx" / "Debug"
            / "obj" / "arm64-v8a"
            / "libsvoyak.so",
        ]

        try:

            for found in jni_dir.rglob(
                "libsvoyak.so"
            ):

                if found not in candidates:

                    candidates.append(
                        found
                    )

        except Exception as error:

            print(
                "Ошибка поиска библиотеки:",
                error
            )

        for candidate in candidates:

            try:

                if not candidate.exists():
                    continue

                if candidate.stat().st_size <= 0:
                    continue

                shutil.copy2(
                    candidate,
                    output
                )

                if (
                    output.exists()
                    and output.stat().st_size > 0
                ):

                    print(
                        "JNI BUILD SUCCESS:",
                        output
                    )

                    return output

            except Exception as error:

                print(
                    "Ошибка копирования:",
                    candidate,
                    error
                )

    except subprocess.TimeoutExpired:

        print(
            "JNI-сборка превысила лимит 900 секунд."
        )

    except Exception as error:

        print(
            "Ошибка JNI-сборки:",
            error
        )

    return None


# =====================================================
# FTP HELPERS
# =====================================================

def ftp_is_directory(ftp, name):
    """
    Проверяет, является ли элемент директорией.
    """

    current = ftp.pwd()

    try:

        ftp.cwd(name)

        ftp.cwd(current)

        return True

    except Exception:

        try:
            ftp.cwd(current)
        except Exception:
            pass

        return False


def ftp_delete_recursive(ftp, path):
    """
    Удаляет конкретную папку со всем содержимым.
    Вызывается ТОЛЬКО для папки, которую бот решил
    заменить из состава нового мода.
    """

    current = ftp.pwd()

    try:
        ftp.cwd(path)
    except Exception:
        return False

    try:

        try:
            items = ftp.nlst()
        except Exception:
            items = []

        for item in items:

            name = os.path.basename(
                item.rstrip("/")
            )

            if not name:
                continue

            if name in (".", ".."):
                continue

            try:

                if ftp_is_directory(
                    ftp,
                    name
                ):

                    ftp_delete_recursive(
                        ftp,
                        name
                    )

                    try:
                        ftp.rmd(name)
                    except Exception:
                        pass

                else:

                    try:
                        ftp.delete(name)
                    except Exception:
                        pass

            except Exception as error:

                print(
                    "FTP delete item error:",
                    name,
                    error
                )

        ftp.cwd("..")

        try:
            ftp.rmd(path)
        except Exception:
            pass

        return True

    except Exception as error:

        print(
            "FTP recursive delete error:",
            path,
            error
        )

        try:
            ftp.cwd(current)
        except Exception:
            pass

        return False


def ftp_delete_item(ftp, name):
    """
    Удаляет один конкретный элемент из FTP.
    Ничего другого не трогает.
    """

    try:

        if name in (".", ".."):
            return False

        # Сначала проверяем папку
        if ftp_is_directory(
            ftp,
            name
        ):

            print(
                "FTP: удаляем старую папку мода:",
                name
            )

            return ftp_delete_recursive(
                ftp,
                name
            )

        # Иначе это файл
        print(
            "FTP: удаляем старый файл мода:",
            name
        )

        try:
            ftp.delete(name)
            return True

        except Exception as error:

            print(
                "FTP: не удалось удалить файл:",
                name,
                error
            )

            return False

    except Exception as error:

        print(
            "FTP delete error:",
            name,
            error
        )

        return False


# =====================================================
# FTP
# =====================================================

def upload_ftp(
    ftp_config,
    local_dir
):

    if not ftp_config:

        return {
            "ok": True,
            "error": None
        }

    ftp = FTP()

    try:

        print(
            f"FTP: подключение к "
            f"{ftp_config['ip']}:{ftp_config['port']}"
        )

        ftp.connect(
            ftp_config["ip"],
            ftp_config["port"],
            timeout=30
        )

        ftp.login(
            ftp_config["login"],
            ftp_config["password"]
        )

        ftp.set_pasv(True)

        # =================================================
        # КОРЕНЬ FTP
        # =================================================

        ftp.cwd("/")

        print(
            "FTP ROOT:",
            ftp.pwd()
        )

        local_path = Path(local_dir)

        # =================================================
        # 1. УЗНАЁМ, ЧТО ИМЕННО ЕСТЬ В МОДЕ
        # =================================================
        #
        # ВАЖНО:
        #
        # Мы НЕ удаляем весь FTP.
        #
        # Удаляем только те элементы корня FTP,
        # которые совпадают по имени с элементами
        # нашего нового мода.
        #
        # Например:
        #
        # FTP:
        #   gamemodes/
        #   filterscripts/
        #   scriptfiles/
        #   чужая_папка/
        #
        # Новый мод:
        #   gamemodes/
        #   filterscripts/
        #   scriptfiles/
        #
        # Будут удалены только:
        #   gamemodes/
        #   filterscripts/
        #   scriptfiles/
        #
        # "чужая_папка/" останется.
        #
        # SQL НЕ участвует в удалении/загрузке.
        # =================================================

        local_top_items = []

        for item in local_path.iterdir():

            if item.name.lower() == "svoyak.sql":
                continue

            local_top_items.append(
                item.name
            )

        print(
            "FTP: элементы нового мода:",
            local_top_items
        )

        # =================================================
        # 2. УДАЛЯЕМ ТОЛЬКО СОВПАДАЮЩИЕ ЭЛЕМЕНТЫ
        # =================================================

        for item_name in local_top_items:

            ftp_delete_item(
                ftp,
                item_name
            )

        # Возвращаемся в корень
        ftp.cwd("/")

        # =================================================
        # 3. СОЗДАНИЕ ПАПКИ
        # =================================================

        def ensure_remote_dir(name):

            try:

                ftp.cwd(name)

                return True

            except Exception:
                pass

            try:

                ftp.mkd(name)

                ftp.cwd(name)

                return True

            except Exception as error:

                print(
                    "FTP MKD ERROR:",
                    name,
                    error
                )

                return False

        # =================================================
        # 4. ЗАГРУЗКА МОДА
        # =================================================

        def upload_directory(local_current):

            local_current = Path(
                local_current
            )

            for item in local_current.iterdir():

                # -----------------------------------------
                # SQL НИКОГДА НЕ ЗАГРУЖАЕМ НА FTP
                # -----------------------------------------

                if (
                    item.is_file()
                    and item.name.lower() == "svoyak.sql"
                ):

                    print(
                        "FTP: SQL пропущен:",
                        item
                    )

                    continue

                # -----------------------------------------
                # ПАПКА
                # -----------------------------------------

                if item.is_dir():

                    if not ensure_remote_dir(
                        item.name
                    ):

                        raise RuntimeError(
                            "Не удалось создать/открыть "
                            f"FTP-папку: {item.name}"
                        )

                    upload_directory(
                        item
                    )

                    ftp.cwd("..")

                # -----------------------------------------
                # ФАЙЛ
                # -----------------------------------------

                else:

                    print(
                        "FTP: загрузка:",
                        item
                    )

                    with open(
                        item,
                        "rb"
                    ) as file:

                        ftp.storbinary(
                            f"STOR {item.name}",
                            file
                        )

        ftp.cwd("/")

        upload_directory(
            local_path
        )

        ftp.cwd("/")

        ftp.quit()

        print(
            "FTP: загрузка завершена."
        )

        return {
            "ok": True,
            "error": None
        }

    except ConnectionRefusedError:

        error_text = (
            "FTP-сервер отказал в подключении "
            "(Connection refused). Проверь IP, порт, "
            "запущен ли FTP-сервис и открыт ли порт."
        )

        print(
            "FTP ERROR:",
            error_text
        )

        try:
            ftp.close()
        except Exception:
            pass

        return {
            "ok": False,
            "error": error_text
        }

    except TimeoutError:

        error_text = (
            "Тайм-аут подключения к FTP. "
            "Проверь IP, порт и firewall."
        )

        print(
            "FTP ERROR:",
            error_text
        )

        try:
            ftp.close()
        except Exception:
            pass

        return {
            "ok": False,
            "error": error_text
        }

    except Exception as error:

        error_text = str(error)

        print(
            "FTP ERROR:",
            error_text
        )

        try:
            ftp.close()
        except Exception:
            pass

        return {
            "ok": False,
            "error": error_text
        }


# =====================================================
# PERFORM BUILD
# =====================================================

def perform_build(
    build,
    build_dir
):

    try:

        # -------------------------------------------------
        # CLEAN MOD
        # -------------------------------------------------

        if not MOD_FILE.exists():

            return {
                "status": "error",
                "error": (
                    "clean_mod.zip отсутствует. "
                    "Администратор должен загрузить его "
                    "через /admin."
                )
            }

        # -------------------------------------------------
        # SQL
        # -------------------------------------------------

        if not SQL_FILE.exists():

            return {
                "status": "error",
                "error": (
                    "svoyak.sql отсутствует. "
                    "Администратор должен загрузить его "
                    "через /admin."
                )
            }

        # -------------------------------------------------
        # JNI
        # -------------------------------------------------

        if not JNI_FILE.exists():

            return {
                "status": "error",
                "error": (
                    "jni_project.zip отсутствует. "
                    "Администратор должен загрузить JNI-проект "
                    "через /admin."
                )
            }

        # -------------------------------------------------
        # BUILD SCRIPT
        # -------------------------------------------------

        if not BUILD_SCRIPT.exists():

            return {
                "status": "error",
                "error": (
                    "build_client.sh отсутствует."
                )
            }

        # -------------------------------------------------
        # PREPARE MOD
        # -------------------------------------------------

        prepared = prepare_mod(
            build,
            build_dir
        )

        if not prepared.get("ok"):

            return {
                "status": "error",
                "error": prepared.get(
                    "error",
                    "Не удалось подготовить мод."
                )
            }

        # -------------------------------------------------
        # SQL
        # -------------------------------------------------

        sql_path = build_dir / "svoyak.sql"

        if not sql_path.exists():

            return {
                "status": "error",
                "error": "svoyak.sql не был создан."
            }

        # -------------------------------------------------
        # JNI BUILD
        # -------------------------------------------------

        lib_path = build_client(
            build,
            build_dir
        )

        if not lib_path:

            return {
                "status": "error",
                "error": (
                    "libsvoyak.so не создана.\n\n"
                    "Проверьте:\n"
                    "🧩 JNI-проект загружен\n"
                    "🧰 build_client.sh существует\n"
                    "🛠 NDK r25c установлен\n"
                    "📱 ABI = arm64-v8a\n"
                    "🔨 JNI-проект действительно собирает "
                    "libsvoyak.so"
                )
            }

        # -------------------------------------------------
        # FTP
        # -------------------------------------------------

        ftp_result = {
            "ok": True,
            "error": None
        }

        if build.get("ftp"):

            ftp_result = upload_ftp(
                build["ftp"],
                prepared["mod_dir"]
            )

            if not ftp_result["ok"]:

                return {
                    "status": "error",
                    "error": (
                        "Мод и библиотека собраны, "
                        "но FTP-загрузка не удалась: "
                        + ftp_result["error"]
                    ),
                    "sql": str(sql_path),
                    "lib": str(lib_path),
                    "ftp_uploaded": False
                }

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        return {
            "status": "success",
            "sql": str(sql_path),
            "lib": str(lib_path),
            "ftp_uploaded": bool(
                build.get("ftp")
            )
        }

    except Exception as error:

        print(
            "BUILD ERROR:",
            error
        )

        return {
            "status": "error",
            "error": str(error)
        }


# =====================================================
# CREATE BUILD
# =====================================================

async def create_build(
    update,
    context,
    data,
    user
):

    user_id = str(
        update.effective_user.id
    )

    build = user.get(
        "free_build"
    )

    if not build:
        return

    build_id = (
        f"{user_id}_"
        f"{int(time.time())}"
    )

    build_dir = BASE_DIR / build_id

    build_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    data["builds"][build_id] = {
        "user_id": user_id,
        "project_name": build["project_name"],
        "status": "building"
    }

    save_data(data)

    await context.bot.send_message(
        chat_id=int(user_id),
        text=(
            "🔨 СБОРКА ПРОЕКТА\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "⏳ Настройки приняты.\n"
            "📦 Проверяю чистый мод.\n"
            "🧰 Подготавливаю мод.\n"
            "🗄 Формирую svoyak.sql.\n"
            "🧩 Распаковываю JNI-проект.\n"
            "📱 Собираю libsvoyak.so.\n"
            "⚙️ ABI: arm64-v8a\n"
            "🛠 NDK: r25c\n\n"
            "Статус: сборка запущена."
        )
    )

    result = await asyncio.to_thread(
        perform_build,
        build,
        build_dir
    )

    data = load_data()

    current_user = get_user(
        data,
        int(user_id)
    )

    status = result.get("status")

    if status != "success":

        current_user["free_build"]["status"] = "error"

        if build_id in data["builds"]:

            data["builds"][build_id]["status"] = "error"

        save_data(data)

        error_text = result.get(
            "error",
            "Неизвестная ошибка."
        )

        await context.bot.send_message(
            chat_id=int(user_id),
            text=(
                "❌ Сборка не завершена.\n\n"
                f"Причина:\n{error_text}\n\n"
                "Проверь настройки и файлы в админ-панели."
            )
        )

        try:

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "❌ ОШИБКА БЕСПЛАТНОЙ СБОРКИ\n\n"
                    f"👤 Telegram ID: {user_id}\n"
                    f"🏷 Проект: {build['project_name']}\n"
                    f"📁 Build ID: {build_id}\n"
                    f"📝 Ошибка: {error_text}"
                )
            )

        except Exception:
            pass

        return

    current_user["free_build"]["status"] = "completed"

    if build_id in data["builds"]:

        data["builds"][build_id]["status"] = "completed"

    if build["project_name"] not in current_user["projects"]:

        current_user["projects"].append(
            build["project_name"]
        )

    save_data(data)

    # =================================================
    # LIBRARY
    # =================================================

    lib_path = result.get("lib")

    if lib_path and os.path.exists(lib_path):

        await context.bot.send_document(
            chat_id=int(user_id),
            document=lib_path,
            caption=(
                "✅ Клиентская библиотека готова\n\n"
                f"🏷 Проект: {build['project_name']}\n"
                f"🌐 Сервер: {build['server']['address']}\n"
                "🧰 Компилятор: NDK r25c\n"
                "📱 ABI: arm64-v8a"
            )
        )

    # =================================================
    # SQL
    # =================================================

    sql_path = result.get("sql")

    if sql_path and os.path.exists(sql_path):

        await context.bot.send_document(
            chat_id=int(user_id),
            document=sql_path,
            caption=(
                "🗄 БАЗА ДАННЫХ ДЛЯ РУЧНОГО ИМПОРТА\n\n"
                "Файл: svoyak.sql\n"
                f"База: {build['mysql']['database']}\n"
                f"👑 Владелец {build['owner']} автоматически "
                "получит 13-й уровень администратора "
                "при создании аккаунта.\n\n"
                "Импортируй этот SQL-файл в свою базу данных вручную."
            )
        )

    # =================================================
    # RESULT
    # =================================================

    ftp_text = ""

    if build.get("ftp"):

        if result.get("ftp_uploaded"):

            ftp_text = (
                "\n\n📁 Мод загружен на FTP.\n"
                "🛡️ Другие папки и файлы FTP не затронуты.\n"
                "🗄 svoyak.sql на FTP не загружался."
            )

    await context.bot.send_message(
        chat_id=int(user_id),
        text=(
            "🎉 СБОРКА ЗАВЕРШЕНА!\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🏷 Проект: {build['project_name']}\n"
            f"🌐 Сервер: {build['server']['address']}\n"
            "📱 Клиентская библиотека: готова\n"
            "🗄 SQL: готов\n"
            "⚙️ ABI: arm64-v8a\n"
            "🛠 NDK: r25c\n"
            f"👑 Владелец: {build['owner']}"
            f"{ftp_text}\n\n"
            "Файлы отправлены выше."
        ),
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


# =====================================================
# ADMIN PANEL
# =====================================================

def admin_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📦 Загрузить чистый мод",
                callback_data="admin_mod"
            )
        ],
        [
            InlineKeyboardButton(
                "🗄 Загрузить svoyak.sql",
                callback_data="admin_sql"
            )
        ],
        [
            InlineKeyboardButton(
                "🧩 Загрузить JNI-проект",
                callback_data="admin_jni"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 Состояние файлов",
                callback_data="admin_status"
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 Главное меню",
                callback_data="main_menu"
            )
        ],
    ])


async def admin_command(
    update,
    context
):

    if update.effective_user.id != ADMIN_ID:
        return

    context.user_data["admin_upload"] = None

    await update.message.reply_text(
        "👑 АДМИН-ПАНЕЛЬ\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Управление файлами сборки:",
        reply_markup=admin_menu()
    )


async def admin_upload_document(
    update,
    context
):

    if update.effective_user.id != ADMIN_ID:
        return

    upload_type = context.user_data.get(
        "admin_upload"
    )

    if not upload_type:
        return

    document = update.message.document

    if not document:
        return

    # -------------------------------------------------
    # MOD
    # -------------------------------------------------

    if upload_type == "mod":

        destination = MOD_FILE

    # -------------------------------------------------
    # SQL
    # -------------------------------------------------

    elif upload_type == "sql":

        destination = SQL_FILE

    # -------------------------------------------------
    # JNI
    # -------------------------------------------------

    elif upload_type == "jni":

        destination = JNI_FILE

        file_name = (
            document.file_name or ""
        )

        if not file_name.lower().endswith(".zip"):

            await update.message.reply_text(
                "❌ JNI-проект должен быть ZIP-архивом.\n\n"
                "Отправь файл вида:\n"
                "jni_project.zip"
            )

            return

    else:

        return

    try:

        file = await document.get_file()

        await file.download_to_drive(
            custom_path=str(destination)
        )

    except Exception as error:

        await update.message.reply_text(
            f"❌ Ошибка загрузки: {error}"
        )

        return

    context.user_data["admin_upload"] = None

    await update.message.reply_text(
        "✅ Файл успешно загружен.\n\n"
        f"📁 {destination.name}",
        reply_markup=admin_menu()
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

    if context.args:

        argument = context.args[0]

        if argument.startswith("ref_"):

            try:

                ref_id = int(
                    argument[4:]
                )

                if ref_id != user.id:

                    if str(ref_id) in data["users"]:

                        if current_user.get("referrer") is None:

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
# BUTTONS
# =====================================================

async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    # =================================================
    # MAIN
    # =================================================

    if query.data == "main_menu":

        name = query.from_user.first_name or "пользователь"

        await query.edit_message_text(
            f"🙂 {name}, привет!\n\n"
            "Собираю готовый мобильный проект Black Russia "
            "под твой сервер: своё название, свои цвета, "
            "своя иконка, свой APK.\n\n"
            "💸 От 399 ⭐   🕓 Сборка ~10 минут   "
            "✅ Всё автоматически\n\n"
            "Мод, база данных и приложение устанавливаются "
            "на твой сервер автоматически — тебе нужно только "
            "ответить на вопросы бота.\n\n"
            "Выбери раздел в меню под строкой ввода.",
            reply_markup=main_menu()
        )

    # =================================================
    # SUPPORT
    # =================================================

    elif query.data == "support":

        await show_support(query)

    # =================================================
    # PARTNER
    # =================================================

    elif query.data == "partner":

        await show_partner(
            query,
            context
        )

    # =================================================
    # PROJECTS
    # =================================================

    elif query.data == "projects":

        await show_projects(query)

    # =================================================
    # SHOP
    # =================================================

    elif query.data == "shop":

        await query.edit_message_text(
            "🪙 МАГАЗИН SVOYAK\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "В одном месте: готовые игровые проекты, "
            "реклама в канале и услуги для владельцев ULTRA.\n\n"
            "Выбери нужный раздел ниже.",
            reply_markup=shop_menu()
        )

    elif query.data == "shop_projects":

        await query.edit_message_text(
            "📦 ПРОЕКТЫ BLACK RUSSIA\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "В магазине два готовых проекта.\n\n"
            "📦 BLACK RUSSIA PRO · ⭐️ 200\n\n"
            "🎁 BLACK RUSSIA ULTIMATE v2.2 · ⭐️ 500\n\n"
            "🪙 Автооплата: Telegram Stars.",
            reply_markup=projects_menu()
        )

    # =================================================
    # PRO
    # =================================================

    elif query.data == "project_pro":

        await query.edit_message_text(
            "📦 BLACK RUSSIA PRO\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "⭐️ 200   🕓 сборка ~10 минут\n\n"
            "Готовый мод с упором на тюнинг и визуал.\n\n"
            "🔓 Доступ откроется сразу после оплаты.",
            reply_markup=pro_menu()
        )

    # =================================================
    # ULTIMATE
    # =================================================

    elif query.data == "project_ultimate":

        await query.edit_message_text(
            "📦 BLACK RUSSIA ULTIMATE v2.2\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "⭐️ 500   🕓 сборка ~10 минут\n\n"
            "Расширенная версия PRO с дополнительными системами.\n\n"
            "🔓 Доступ откроется сразу после оплаты.",
            reply_markup=ultimate_menu()
        )

    # =================================================
    # COMPARE
    # =================================================

    elif query.data == "project_compare":

        await query.edit_message_text(
            "👁 PRO ИЛИ ULTIMATE v2.2\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "📦 BLACK RUSSIA PRO · 200 🌟\n"
            "📦 BLACK RUSSIA ULTIMATE · 500 🌟",
            reply_markup=compare_menu()
        )

    # =================================================
    # FREE
    # =================================================

    elif query.data == "free":

        await start_free_build(query)

    # =================================================
    # BUILD
    # =================================================

    elif query.data == "build":

        await query.edit_message_text(
            "🔨 СБОРКА ПРОЕКТА\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Оплаченных запусков пока нет.\n\n"
            "Купи BLACK RUSSIA PRO или ULTIMATE v2.2 — "
            "и студия откроется сразу после оплаты. "
            "Бесплатная сборка доступна кнопкой "
            "«Бесплатный проект» в меню.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🛒 Купить проект",
                        callback_data="shop"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🆓 Бесплатный проект",
                        callback_data="free"
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
    # ADS
    # =================================================

    elif query.data == "shop_ads":

        await query.edit_message_text(
            "📢 РЕКЛАМА В КАНАЛЕ\n\n"
            "Здесь будут тарифы на рекламу.",
            reply_markup=back_menu("shop")
        )

    # =================================================
    # BUY PRO
    # =================================================

    elif query.data == "buy_pro":

        await send_project_invoice(
            update,
            context,
            "BLACK RUSSIA PRO",
            200
        )

    # =================================================
    # BUY ULTIMATE
    # =================================================

    elif query.data == "buy_ultimate":

        await send_project_invoice(
            update,
            context,
            "BLACK RUSSIA ULTIMATE v2.2",
            500
        )

    # =================================================
    # ADMIN PANEL
    # =================================================

    elif query.data == "admin_panel":

        if query.from_user.id != ADMIN_ID:
            return

        await query.edit_message_text(
            "👑 АДМИН-ПАНЕЛЬ\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Управление файлами сборки:",
            reply_markup=admin_menu()
        )

    # =================================================
    # ADMIN ACTIONS
    # =================================================

    elif query.data.startswith("admin_"):

        if query.from_user.id != ADMIN_ID:
            return

        if query.data == "admin_mod":

            context.user_data["admin_upload"] = "mod"

            await query.edit_message_text(
                "📦 ЗАГРУЗКА ЧИСТОГО МОДА\n\n"
                "Отправь ZIP-архив с чистым модом.\n\n"
                "Файл будет сохранён как:\n"
                "admin_files/clean_mod.zip",
                reply_markup=back_menu("admin_panel")
            )

        elif query.data == "admin_sql":

            context.user_data["admin_upload"] = "sql"

            await query.edit_message_text(
                "🗄 ЗАГРУЗКА SVOYAK.SQL\n\n"
                "Отправь файл:\n"
                "svoyak.sql",
                reply_markup=back_menu("admin_panel")
            )

        elif query.data == "admin_jni":

            context.user_data["admin_upload"] = "jni"

            await query.edit_message_text(
                "🧩 ЗАГРУЗКА JNI-ПРОЕКТА\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "Отправь ZIP-архив с JNI-проектом.\n\n"
                "Например:\n"
                "jni_project.zip\n\n"
                "Внутри должны находиться исходники JNI "
                "и файлы сборки CMake/ndk-build.\n\n"
                "После загрузки бот автоматически будет "
                "собирать:\n\n"
                "📱 libsvoyak.so\n"
                "⚙️ ABI: arm64-v8a\n"
                "🛠 NDK: r25c\n\n"
                "IP и PORT сервера будут переданы "
                "в процесс сборки.",
                reply_markup=back_menu("admin_panel")
            )

        elif query.data == "admin_status":

            mod_status = (
                "✅ загружен"
                if MOD_FILE.exists()
                else "❌ отсутствует"
            )

            sql_status = (
                "✅ загружен"
                if SQL_FILE.exists()
                else "❌ отсутствует"
            )

            jni_status = (
                "✅ загружен"
                if JNI_FILE.exists()
                else "❌ отсутствует"
            )

            build_status = (
                "✅ найден"
                if BUILD_SCRIPT.exists()
                else "❌ отсутствует"
            )

            await query.edit_message_text(
                "📊 ФАЙЛЫ SVOYAK\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📦 clean_mod.zip — {mod_status}\n"
                f"🗄 svoyak.sql — {sql_status}\n"
                f"🧩 jni_project.zip — {jni_status}\n"
                f"🧰 build_client.sh — {build_status}\n\n"
                "Для сборки нужны:\n"
                "📦 clean_mod.zip\n"
                "🗄 svoyak.sql\n"
                "🧩 jni_project.zip\n"
                "🧰 build_client.sh\n\n"
                "⚙️ ABI: arm64-v8a\n"
                "🛠 NDK: r25c\n\n"
                "Готовый libsvoyak.so загружать НЕ нужно — "
                "бот собирает его из JNI-проекта автоматически.",
                reply_markup=admin_menu()
            )


# =====================================================
# PAYMENT
# =====================================================

async def send_project_invoice(
    update,
    context,
    project_name,
    stars
):

    user = update.effective_user

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
        prices=[
            LabeledPrice(
                label=project_name,
                amount=stars
            )
        ]
    )


async def precheckout_callback(
    update,
    context
):

    await update.pre_checkout_query.answer(
        ok=True
    )


async def successful_payment(
    update,
    context
):

    payment = update.message.successful_payment

    user = update.effective_user

    payload = payment.invoice_payload

    if not payload.startswith("project:"):
        return

    parts = payload.split(":", 2)

    if len(parts) != 3:
        return

    project_name = parts[1]

    stars = payment.total_amount

    data = load_data()

    buyer = get_user(
        data,
        user.id
    )

    if project_name not in buyer["projects"]:

        buyer["projects"].append(
            project_name
        )

    buyer["has_purchased"] = True

    referrer_id = buyer.get("referrer")

    if referrer_id:

        referrer = get_user(
            data,
            referrer_id
        )

        if referrer.get(
            "has_purchased",
            False
        ):

            referral_profit = int(
                stars * 0.15
            )

            referrer["balance"] += referral_profit
            referrer["total_profit"] += referral_profit
            referrer["monthly_profit"] += referral_profit
            referrer["weekly_profit"] += referral_profit
            referrer["today_profit"] += referral_profit

    save_data(data)

    await update.message.reply_text(
        "✅ ОПЛАТА ПОЛУЧЕНА!\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 Проект: {project_name}\n"
        f"🪙 Оплачено: {stars} ⭐\n\n"
        "📁 Проект добавлен в «Мои проекты».\n"
        "🔓 Заказ закреплён за твоим Telegram.",
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

    try:

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "💰 НОВАЯ ОПЛАТА\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 Пользователь: {user.first_name}\n"
                f"🆔 Telegram ID: {user.id}\n"
                f"📦 Проект: {project_name}\n"
                f"🪙 Сумма: {stars} ⭐"
            )
        )

    except Exception as error:

        print(
            "Ошибка уведомления админу:",
            error
        )


# =====================================================
# RUN
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
        CommandHandler(
            "admin",
            admin_command
        )
    )

    # -------------------------------------------------
    # АДМИНСКИЕ ФАЙЛЫ
    # -------------------------------------------------

    app.add_handler(
        MessageHandler(
            filters.Document.ALL,
            admin_upload_document
        )
    )

    # -------------------------------------------------
    # БЕСПЛАТНАЯ СБОРКА
    # -------------------------------------------------

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            free_build_message
        )
    )

    # -------------------------------------------------
    # CALLBACK BUTTONS
    # -------------------------------------------------

    app.add_handler(
        CallbackQueryHandler(
            buttons
        )
    )

    # -------------------------------------------------
    # PAYMENT
    # -------------------------------------------------

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

    print(
        "SVOYAK BOT запущен!"
    )

    app.run_polling()


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    run()
