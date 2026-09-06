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

JNI_FILE = ADMIN_FILES_DIR / "jni_project.zip"
JNI_DIR = ADMIN_FILES_DIR / "jni_project"

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
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        data.setdefault("users", {})
        data.setdefault("builds", {})

        return data

    except Exception:
        return {
            "users": {},
            "builds": {}
        }


def save_data(data):
    temp_file = DATA_FILE + ".tmp"

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
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
            "free_build": False,
            "blocked": False
        }

    user = data["users"][user_id]

    user.setdefault("referrer", None)
    user.setdefault("projects", [])
    user.setdefault("balance", 0)
    user.setdefault("total_profit", 0)
    user.setdefault("monthly_profit", 0)
    user.setdefault("weekly_profit", 0)
    user.setdefault("yesterday_profit", 0)
    user.setdefault("today_profit", 0)
    user.setdefault("referrals", [])
    user.setdefault("has_purchased", False)
    user.setdefault("free_build", False)
    user.setdefault("blocked", False)

    return user


# =====================================================
# WEB HEALTH
# =====================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header(
            "Content-Type",
            "text/plain; charset=utf-8"
        )
        self.end_headers()

        self.wfile.write(
            b"SVOYAK BOT is running!"
        )

    def log_message(self, format, *args):
        return


def run_web_server():
    port = int(
        os.getenv("PORT", "10000")
    )

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    server.serve_forever()


# =====================================================
# МЕНЮ
# =====================================================

def main_menu(user_id=None):

    buttons = [
        [
            InlineKeyboardButton(
                "🛒 Магазин",
                callback_data="shop"
            )
        ],
        [
            InlineKeyboardButton(
                "🆓 Бесплатный проект",
                callback_data="free_build"
            )
        ],
        [
            InlineKeyboardButton(
                "⚙️ Сборка",
                callback_data="build"
            )
        ],
        [
            InlineKeyboardButton(
                "📂 Мои проекты",
                callback_data="projects"
            )
        ],
        [
            InlineKeyboardButton(
                "🆘 Поддержка",
                callback_data="support"
            )
        ],
        [
            InlineKeyboardButton(
                "🤝 Партнёрка",
                callback_data="partner"
            )
        ],
    ]

    if user_id == ADMIN_ID:
        buttons.append([
            InlineKeyboardButton(
                "👑 Админ-панель",
                callback_data="admin_panel"
            )
        ])

    return InlineKeyboardMarkup(buttons)


def back_menu(callback="main_menu"):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data=callback
            )
        ]
    ])


# =====================================================
# МАГАЗИН
# =====================================================

def shop_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "⭐ PRO",
                callback_data="pro"
            )
        ],
        [
            InlineKeyboardButton(
                "💎 ULTIMATE",
                callback_data="ultimate"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 Сравнить",
                callback_data="compare"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="main_menu"
            )
        ]
    ])


def pro_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💳 Купить PRO",
                callback_data="buy_pro"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="shop"
            )
        ]
    ])


def ultimate_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💳 Купить ULTIMATE",
                callback_data="buy_ultimate"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="shop"
            )
        ]
    ])


def compare_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="shop"
            )
        ]
    ])


# =====================================================
# АДМИНКА
# =====================================================

def admin_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📦 Загрузить мод",
                callback_data="admin_mod"
            )
        ],
        [
            InlineKeyboardButton(
                "🗄 Загрузить SQL",
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
                "📋 Статус файлов",
                callback_data="admin_status"
            )
        ],
        [
            InlineKeyboardButton(
                "👥 Пользователи",
                callback_data="admin_users"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 Статистика",
                callback_data="admin_stats"
            )
        ],
        [
            InlineKeyboardButton(
                "💰 Управление очками",
                callback_data="admin_points"
            )
        ],
        [
            InlineKeyboardButton(
                "📢 Рассылка",
                callback_data="admin_broadcast"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="main_menu"
            )
        ]
    ])


# =====================================================
# START
# =====================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    data = load_data()

    db_user = get_user(
        data,
        user.id
    )

    if db_user.get("blocked") and user.id != ADMIN_ID:
        await update.message.reply_text(
            "🚫 Твой аккаунт заблокирован."
        )
        return

    # Реферал
    if context.args:

        arg = context.args[0]

        if arg.startswith("ref_"):

            try:

                referrer_id = int(
                    arg.replace("ref_", "")
                )

                if (
                    referrer_id != user.id
                    and not db_user["referrer"]
                ):

                    db_user["referrer"] = referrer_id

                    referrer = get_user(
                        data,
                        referrer_id
                    )

                    if user.id not in referrer["referrals"]:
                        referrer["referrals"].append(
                            user.id
                        )

                    save_data(data)

            except Exception:
                pass

    save_data(data)

    text = (
        "🤖 <b>SVOYAK</b>\n\n"
        "Добро пожаловать!\n\n"
        "Здесь можно создать свой игровой проект, "
        "подготовить мод и собрать клиентскую библиотеку.\n\n"
        "Выбери нужный раздел ниже 👇"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=main_menu(user.id)
    )


# =====================================================
# ADMIN COMMAND
# =====================================================

async def admin_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        "👑 <b>Админ-панель SVOYAK</b>",
        parse_mode="HTML",
        reply_markup=admin_menu()
    )


# =====================================================
# SUPPORT
# =====================================================

async def support(update, context):

    text = (
        "🆘 <b>Поддержка</b>\n\n"
        "Если у тебя возникла проблема с проектом "
        "или сборкой — напиши в поддержку."
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💬 Поддержка",
                url="https://t.me/svoyak_support_bot"
            )
        ],
        [
            InlineKeyboardButton(
                "📜 Пользовательское соглашение",
                url="https://telegra.ph/"
            )
        ],
        [
            InlineKeyboardButton(
                "🔐 Политика конфиденциальности",
                url="https://telegra.ph/"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="main_menu"
            )
        ]
    ])

    await update.callback_query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


# =====================================================
# ПАРТНЁРКА
# =====================================================

async def partner(update, context):

    user = update.effective_user

    try:

        bot_user = await context.bot.get_me()

        link = (
            f"https://t.me/{bot_user.username}"
            f"?start=ref_{user.id}"
        )

    except Exception:

        link = "Ссылка временно недоступна."

    data = load_data()

    db_user = get_user(
        data,
        user.id
    )

    referrals = len(
        db_user["referrals"]
    )

    balance = db_user["balance"]

    text = (
        "🤝 <b>Партнёрская программа</b>\n\n"
        "Приглашай пользователей по своей ссылке.\n\n"
        "💰 Доход: <b>15%</b> с покупки приглашённого "
        "пользователя.\n\n"
        f"👥 Приглашено: <b>{referrals}</b>\n"
        f"💰 Баланс: <b>{balance}</b>\n\n"
        f"🔗 Твоя ссылка:\n<code>{link}</code>"
    )

    await update.callback_query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=back_menu()
    )


# =====================================================
# ПРОЕКТЫ
# =====================================================

async def projects(update, context):

    user = update.effective_user

    data = load_data()

    db_user = get_user(
        data,
        user.id
    )

    projects_list = db_user["projects"]

    if not projects_list:

        text = (
            "📂 <b>Мои проекты</b>\n\n"
            "У тебя пока нет проектов."
        )

    else:

        lines = [
            "📂 <b>Мои проекты</b>\n"
        ]

        for index, project in enumerate(
            projects_list,
            1
        ):

            if isinstance(project, dict):

                name = project.get(
                    "name",
                    "Без названия"
                )

                server = project.get(
                    "server",
                    "Не указан"
                )

                lines.append(
                    f"{index}. <b>{name}</b> — "
                    f"<code>{server}</code>"
                )

            else:

                lines.append(
                    f"{index}. {project}"
                )

        text = "\n".join(lines)

    await update.callback_query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=back_menu()
    )


# =====================================================
# FREE BUILD
# =====================================================

async def free_build_start(update, context):

    context.user_data["free_build"] = {
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

    await update.callback_query.edit_message_text(
        "🆓 <b>Бесплатный проект</b>\n\n"
        "Шаг 1 из 7.\n\n"
        "🌐 Введи IP и порт сервера в формате:\n"
        "<code>127.0.0.1:7777</code>",
        parse_mode="HTML",
        reply_markup=back_menu()
    )


def valid_server(value):

    value = value.strip()

    if ":" not in value:
        return False

    ip, port = value.rsplit(":", 1)

    if not ip or not port:
        return False

    try:
        port = int(port)
    except ValueError:
        return False

    return 1 <= port <= 65535


def parse_bonuses(value):

    parts = value.replace(",", " ").split()

    if len(parts) != 4:
        return None

    try:

        numbers = [
            int(x)
            for x in parts
        ]

    except ValueError:
        return None

    if any(x < 0 for x in numbers):
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


def parse_mysql(value):

    parts = value.split()

    if len(parts) < 4:
        return None

    return {
        "host": parts[0],
        "username": parts[1],
        "password": " ".join(parts[2:-1]),
        "database": parts[-1]
    }


def parse_ftp(value):

    parts = value.split()

    if len(parts) != 3:
        return None

    address = parts[0]

    if ":" not in address:
        return None

    ip, port = address.rsplit(":", 1)

    try:
        port = int(port)
    except ValueError:
        return None

    if port < 1 or port > 65535:
        return None

    return {
        "host": ip,
        "port": port,
        "username": parts[1],
        "password": parts[2]
    }


# =====================================================
# FREE BUILD MESSAGE
# =====================================================

async def free_build_message(
    update,
    context
):

    if not update.message:
        return

    user = update.effective_user

    value = update.message.text.strip()

    state = context.user_data.get(
        "free_build"
    )

    if not state:
        return

    data = load_data()

    db_user = get_user(
        data,
        user.id
    )

    if db_user.get("blocked") and user.id != ADMIN_ID:

        await update.message.reply_text(
            "🚫 Твой аккаунт заблокирован."
        )

        return

    step = state.get("step")

    # -------------------------------------------------
    # ШАГ 1
    # -------------------------------------------------

    if step == 1:

        if not valid_server(value):

            await update.message.reply_text(
                "❌ Неверный формат.\n\n"
                "Используй:\n"
                "<code>127.0.0.1:7777</code>",
                parse_mode="HTML"
            )

            return

        state["server"] = value
        state["step"] = 2

        await update.message.reply_text(
            "✅ Сервер сохранён.\n\n"
            "Шаг 2 из 7.\n\n"
            "📝 Введи название проекта."
        )

        return

    # -------------------------------------------------
    # ШАГ 2
    # -------------------------------------------------

    if step == 2:

        if len(value) < 2:

            await update.message.reply_text(
                "❌ Название слишком короткое."
            )

            return

        state["project_name"] = value
        state["step"] = 3

        await update.message.reply_text(
            "Шаг 3 из 7.\n\n"
            "🎁 Введи бонусы в формате:\n\n"
            "<code>донат деньги VIP уровень</code>\n\n"
            "Например:\n"
            "<code>1000 50000 3 5</code>",
            parse_mode="HTML"
        )

        return

    # -------------------------------------------------
    # ШАГ 3
    # -------------------------------------------------

    if step == 3:

        bonuses = parse_bonuses(value)

        if not bonuses:

            await update.message.reply_text(
                "❌ Неверный формат.\n\n"
                "Нужно 4 числа:\n"
                "<code>донат деньги VIP уровень</code>",
                parse_mode="HTML"
            )

            return

        state["bonuses"] = bonuses
        state["step"] = 4

        await update.message.reply_text(
            "Шаг 4 из 7.\n\n"
            "🔗 Введи ссылки в таком порядке:\n\n"
            "<code>Telegram VK Сайт</code>",
            parse_mode="HTML"
        )

        return

    # -------------------------------------------------
    # ШАГ 4
    # -------------------------------------------------

    if step == 4:

        links = parse_links(value)

        if not links:

            await update.message.reply_text(
                "❌ Нужно указать 3 ссылки:\n"
                "Telegram VK Сайт"
            )

            return

        state["links"] = links
        state["step"] = 5

        await update.message.reply_text(
            "Шаг 5 из 7.\n\n"
            "👤 Введи ник владельца проекта."
        )

        return

    # -------------------------------------------------
    # ШАГ 5
    # -------------------------------------------------

    if step == 5:

        if len(value) < 2:

            await update.message.reply_text(
                "❌ Ник слишком короткий."
            )

            return

        state["owner"] = value
        state["step"] = 6

        await update.message.reply_text(
            "Шаг 6 из 7.\n\n"
            "🗄 Введи данные MySQL:\n\n"
            "<code>HOST USER PASSWORD DATABASE</code>\n\n"
            "Например:\n"
            "<code>127.0.0.1 root 123456 svoyak</code>\n\n"
            "⚠️ Сообщение с паролем будет удалено.",
            parse_mode="HTML"
        )

        return

    # -------------------------------------------------
    # ШАГ 6
    # -------------------------------------------------

    if step == 6:

        mysql = parse_mysql(value)

        if not mysql:

            await update.message.reply_text(
                "❌ Неверный формат MySQL.\n\n"
                "Используй:\n"
                "<code>HOST USER PASSWORD DATABASE</code>",
                parse_mode="HTML"
            )

            return

        state["mysql"] = mysql
        state["step"] = 7

        try:
            await update.message.delete()
        except Exception:
            pass

        await context.bot.send_message(
            chat_id=user.id,
            text=(
                "Шаг 7 из 7.\n\n"
                "📁 Если у тебя есть FTP, отправь:\n\n"
                "<code>IP:PORT LOGIN PASSWORD</code>\n\n"
                "Например:\n"
                "<code>127.0.0.1:21 admin 123456</code>\n\n"
                "Если FTP не нужен — напиши:\n"
                "<code>пропустить</code>\n\n"
                "📁 Подготовленный мод будет загружен "
                "в корень FTP.\n\n"
                "🗄 <b>svoyak.sql на FTP НЕ загружается.</b>\n"
                "После сборки SQL будет отправлен тебе "
                "отдельным файлом для ручного импорта."
            ),
            parse_mode="HTML"
        )

        return

    # -------------------------------------------------
    # ШАГ 7
    # -------------------------------------------------

    if step == 7:

        if value.lower() == "пропустить":

            state["ftp"] = None

        else:

            ftp = parse_ftp(value)

            if not ftp:

                await update.message.reply_text(
                    "❌ Неверный формат FTP.\n\n"
                    "Используй:\n"
                    "<code>IP:PORT LOGIN PASSWORD</code>\n\n"
                    "Или напиши:\n"
                    "<code>пропустить</code>",
                    parse_mode="HTML"
                )

                return

            state["ftp"] = ftp

        try:
            await update.message.delete()
        except Exception:
            pass

        await create_build(
            update,
            context,
            user.id,
            state
        )

        context.user_data.pop(
            "free_build",
            None
        )


# =====================================================
# ЗАМЕНА ТЕКСТА
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

    original = text

    for old, new in replacements.items():

        text = text.replace(
            old,
            str(new)
        )

    if text != original:

        file_path.write_text(
            text,
            encoding="utf-8"
        )

        return True

    return False


# =====================================================
# GENERATE SQL
# =====================================================

def generate_sql(
    build,
    build_dir
):

    if not SQL_FILE.exists():
        return None

    sql_path = build_dir / "svoyak.sql"

    shutil.copy2(
        SQL_FILE,
        sql_path
    )

    mysql = build["mysql"]

    replacements = {
        "YOUR_DB_HOST": mysql["host"],
        "YOUR_DB_USER": mysql["username"],
        "YOUR_DB_PASSWORD": mysql["password"],
        "YOUR_DB_NAME": mysql["database"],

        "PROJECT_NAME": build["project_name"],
        "OWNER_NICK": build["owner"],
        "SERVER_ADDRESS": build["server"],

        "{{DB_HOST}}": mysql["host"],
        "{{DB_USER}}": mysql["username"],
        "{{DB_PASSWORD}}": mysql["password"],
        "{{DB_NAME}}": mysql["database"],

        "{{PROJECT_NAME}}": build["project_name"],
        "{{OWNER_NICK}}": build["owner"],
        "{{SERVER_ADDRESS}}": build["server"],
    }

    replace_in_file(
        sql_path,
        replacements
    )

    return sql_path


# =====================================================
# PREPARE MOD
# =====================================================

def prepare_mod(
    build,
    build_dir
):

    if not MOD_FILE.exists():

        raise RuntimeError(
            "Файл clean_mod.zip не загружен."
        )

    mod_dir = build_dir / "mod"

    if mod_dir.exists():
        shutil.rmtree(mod_dir)

    mod_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # Безопасное извлечение ZIP
    with zipfile.ZipFile(
        MOD_FILE,
        "r"
    ) as archive:

        root = mod_dir.resolve()

        for member in archive.infolist():

            target = (
                mod_dir /
                member.filename
            ).resolve()

            try:
                target.relative_to(root)
            except ValueError:
                raise RuntimeError(
                    "Обнаружен опасный путь в ZIP."
                )

        archive.extractall(
            mod_dir
        )

    mysql = build["mysql"]
    bonuses = build["bonuses"]
    links = build["links"]

    server_ip, server_port = build[
        "server"
    ].rsplit(":", 1)

    replacements = {
        "YOUR_DB_HOST": mysql["host"],
        "YOUR_DB_USER": mysql["username"],
        "YOUR_DB_PASSWORD": mysql["password"],
        "YOUR_DB_NAME": mysql["database"],

        "{{DB_HOST}}": mysql["host"],
        "{{DB_USER}}": mysql["username"],
        "{{DB_PASSWORD}}": mysql["password"],
        "{{DB_NAME}}": mysql["database"],

        "PROJECT_NAME": build["project_name"],
        "{{PROJECT_NAME}}": build["project_name"],

        "OWNER_NICK": build["owner"],
        "{{OWNER_NICK}}": build["owner"],

        "SERVER_ADDRESS": build["server"],
        "{{SERVER_ADDRESS}}": build["server"],

        "{{SERVER_IP}}": server_ip,
        "{{SERVER_PORT}}": server_port,

        "{{TELEGRAM}}": links["telegram"],
        "{{VK}}": links["vk"],
        "{{WEBSITE}}": links["website"],

        "{{DONATE}}": bonuses["donate"],
        "{{MONEY}}": bonuses["money"],
        "{{VIP}}": bonuses["vip"],
        "{{LEVEL}}": bonuses["level"],
    }

    text_extensions = {
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
        ".xml",
        ".gradle",
        ".properties",
        ".mk",
        ".cmake",
        ".java",
        ".kt",
        ".js",
    }

    for file_path in mod_dir.rglob("*"):

        if not file_path.is_file():
            continue

        # SQL отдельно не обрабатываем
        if file_path.suffix.lower() == ".sql":
            continue

        if file_path.suffix.lower() not in text_extensions:
            continue

        replace_in_file(
            file_path,
            replacements
        )

    # SQL создаётся отдельно
    sql_path = generate_sql(
        build,
        build_dir
    )

    # Полностью удаляем SQL из FTP-мода
    for sql_file in mod_dir.rglob("*"):

        if not sql_file.is_file():
            continue

        if sql_file.suffix.lower() == ".sql":

            try:
                sql_file.unlink()
            except Exception:
                pass

    return {
        "mod_dir": mod_dir,
        "sql_path": sql_path
    }


# =====================================================
# JNI PROJECT
# =====================================================

def prepare_jni_project():

    if not JNI_FILE.exists():

        raise RuntimeError(
            "Файл jni_project.zip не загружен."
        )

    if JNI_DIR.exists():
        shutil.rmtree(JNI_DIR)

    JNI_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with zipfile.ZipFile(
        JNI_FILE,
        "r"
    ) as archive:

        root = JNI_DIR.resolve()

        for member in archive.infolist():

            target = (
                JNI_DIR /
                member.filename
            ).resolve()

            try:
                target.relative_to(root)
            except ValueError:
                raise RuntimeError(
                    "Обнаружен опасный путь в JNI ZIP."
                )

        archive.extractall(
            JNI_DIR
        )

    entries = list(
        JNI_DIR.iterdir()
    )

    if (
        len(entries) == 1
        and entries[0].is_dir()
    ):

        project_dir = entries[0]

    else:

        project_dir = JNI_DIR

    return {
        "ok": True,
        "dir": project_dir
    }


# =====================================================
# GRADLE WRAPPER
# =====================================================

def find_gradle_wrapper(
    project_dir
):

    possible = [
        project_dir / "gradlew",
        project_dir / "android" / "gradlew",
    ]

    for path in possible:

        if path.exists() and path.is_file():
            return path

    found = list(
        project_dir.rglob("gradlew")
    )

    for path in found:

        if path.is_file():
            return path

    return None


# =====================================================
# JNI BUILD
# =====================================================

def build_client(
    build,
    build_dir
):

    prepared_jni = prepare_jni_project()

    project_dir = prepared_jni["dir"]

    gradlew = find_gradle_wrapper(
        project_dir
    )

    if not gradlew:

        raise RuntimeError(
            "В jni_project.zip не найден gradlew.\n\n"
            "Добавь полноценный Gradle/JNI проект "
            "с файлом gradlew."
        )

    try:

        os.chmod(
            gradlew,
            0o755
        )

    except Exception:
        pass

    server_ip, server_port = build[
        "server"
    ].rsplit(":", 1)

    env = os.environ.copy()

    env["SERVER_IP"] = server_ip
    env["SERVER_PORT"] = server_port
    env["SERVER_ADDRESS"] = build["server"]

    env["PROJECT_NAME"] = build["project_name"]
    env["OWNER_NICK"] = build["owner"]

    env["ANDROID_ABI"] = "arm64-v8a"
    env["ANDROID_NDK_VERSION"] = "r25c"

    env["SVOYAK_BUILD_DIR"] = str(
        build_dir.resolve()
    )

    # =================================================
    # СБОРКА БЕЗ build_client.sh
    # =================================================

    commands = [
        [
            str(gradlew),
            "assembleRelease"
        ],
        [
            str(gradlew),
            "assembleDebug"
        ],
    ]

    last_output = ""

    build_success = False

    for command in commands:

        try:

            result = subprocess.run(
                command,
                cwd=project_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=900
            )

            last_output = (
                result.stdout
                + "\n"
                + result.stderr
            )

            if result.returncode == 0:

                build_success = True
                break

        except subprocess.TimeoutExpired:

            raise RuntimeError(
                "Сборка JNI превысила 15 минут."
            )

    if not build_success:

        raise RuntimeError(
            "Ошибка Gradle/JNI сборки:\n\n"
            + last_output[-8000:]
        )

    # =================================================
    # ПОИСК LIBSVOYAK.SO
    # =================================================

    candidates = []

    search_dirs = [
        project_dir / "app" / "build",
        project_dir / "build",
        project_dir,
    ]

    for base in search_dirs:

        if not base.exists():
            continue

        try:

            candidates.extend(
                base.rglob("libsvoyak.so")
            )

        except Exception:
            pass

    # Если название отличается,
    # ищем любую .so
    if not candidates:

        for base in search_dirs:

            if not base.exists():
                continue

            try:

                candidates.extend(
                    base.rglob("*.so")
                )

            except Exception:
                pass

    if not candidates:

        raise RuntimeError(
            "Сборка завершилась, "
            "но .so библиотека не найдена."
        )

    # Приоритет arm64-v8a
    arm64_candidates = [
        x for x in candidates
        if "arm64-v8a" in str(x)
    ]

    if arm64_candidates:
        source = arm64_candidates[0]
    else:
        source = candidates[0]

    output = (
        build_dir /
        "libsvoyak.so"
    )

    shutil.copy2(
        source,
        output
    )

    return output


# =====================================================
# FTP
# =====================================================

def ftp_connect(
    ftp_config
):

    ftp = FTP()

    ftp.connect(
        ftp_config["host"],
        ftp_config["port"],
        timeout=30
    )

    ftp.login(
        ftp_config["username"],
        ftp_config["password"]
    )

    ftp.set_pasv(True)

    return ftp


def ftp_name(value):

    value = str(value)

    value = value.rstrip("/")

    return os.path.basename(value)


def delete_remote_tree(
    ftp,
    name
):

    name = ftp_name(name)

    if not name or name in (
        ".",
        ".."
    ):
        return

    parent = ftp.pwd()

    # -------------------------------------------------
    # Пробуем открыть как директорию
    # -------------------------------------------------

    try:

        ftp.cwd(name)

    except Exception:

        # Не папка — удаляем как файл
        try:
            ftp.cwd(parent)
        except Exception:
            pass

        try:

            ftp.delete(name)

            return

        except Exception as e:

            raise RuntimeError(
                f"Не удалось удалить FTP-файл "
                f"{name}: {e}"
            )

    # -------------------------------------------------
    # Мы внутри директории
    # -------------------------------------------------

    try:

        try:
            entries = ftp.nlst()
        except Exception:
            entries = []

        for entry in entries:

            child = ftp_name(entry)

            if child in (
                "",
                ".",
                ".."
            ):
                continue

            delete_remote_tree(
                ftp,
                child
            )

        ftp.cwd("..")

        ftp.rmd(name)

    except Exception:

        try:
            ftp.cwd(parent)
        except Exception:
            pass

        raise


def get_remote_names(ftp):

    try:

        entries = ftp.nlst()

    except Exception:

        return []

    names = []

    for entry in entries:

        name = ftp_name(entry)

        if name and name not in (
            ".",
            ".."
        ):

            names.append(name)

    return names


def has_uploadable_content(
    path
):

    path = Path(path)

    if not path.exists():
        return False

    for item in path.iterdir():

        if item.is_dir():

            if has_uploadable_content(item):
                return True

        elif item.is_file():

            if item.suffix.lower() != ".sql":
                return True

    return False


def upload_ftp(
    ftp_config,
    local_dir
):

    ftp = ftp_connect(
        ftp_config
    )

    uploaded = 0
    deleted = 0

    try:

        ftp.cwd("/")

        local_dir = Path(
            local_dir
        )

        # =================================================
        # 1. Определяем, что именно новый мод заменит
        # =================================================

        local_items = []

        for item in local_dir.iterdir():

            # SQL не участвует
            if (
                item.is_file()
                and item.suffix.lower() == ".sql"
            ):
                continue

            if item.is_dir():

                if not has_uploadable_content(
                    item
                ):
                    continue

                local_items.append(item)

            elif item.is_file():

                local_items.append(item)

        remote_names = set(
            get_remote_names(ftp)
        )

        # =================================================
        # 2. УДАЛЯЕМ СТАРЫЕ ВЕРСИИ
        #
        # ВАЖНО:
        # остальные папки/файлы FTP НЕ ТРОГАЕМ.
        # =================================================

        for item in local_items:

            name = item.name

            if name not in remote_names:
                continue

            try:

                ftp.cwd("/")

                delete_remote_tree(
                    ftp,
                    name
                )

                deleted += 1

                ftp.cwd("/")

            except Exception as e:

                raise RuntimeError(
                    f"Не удалось заменить старый "
                    f"FTP-объект {name}: {e}"
                )

        # =================================================
        # 3. СОЗДАНИЕ ПАПОК
        # =================================================

        def ensure_remote_dir(name):

            try:

                ftp.cwd(name)
                return

            except Exception:
                pass

            try:

                ftp.mkd(name)

            except Exception:
                pass

            ftp.cwd(name)

        # =================================================
        # 4. ЗАГРУЗКА
        # =================================================

        def upload_directory(
            local_path
        ):

            nonlocal uploaded

            local_path = Path(
                local_path
            )

            for item in local_path.iterdir():

                # -----------------------------------------
                # ПАПКА
                # -----------------------------------------

                if item.is_dir():

                    if not has_uploadable_content(
                        item
                    ):
                        continue

                    ensure_remote_dir(
                        item.name
                    )

                    upload_directory(
                        item
                    )

                    ftp.cwd("..")

                    continue

                # -----------------------------------------
                # ФАЙЛ
                # -----------------------------------------

                if not item.is_file():
                    continue

                # SQL НИКОГДА НЕ ЗАГРУЖАЕМ
                if item.suffix.lower() == ".sql":
                    continue

                with open(
                    item,
                    "rb"
                ) as file:

                    ftp.storbinary(
                        f"STOR {item.name}",
                        file
                    )

                uploaded += 1

        ftp.cwd("/")

        upload_directory(
            local_dir
        )

        ftp.cwd("/")

        return {
            "uploaded": uploaded,
            "deleted": deleted
        }

    finally:

        try:
            ftp.quit()
        except Exception:

            try:
                ftp.close()
            except Exception:
                pass


# =====================================================
# PERFORM BUILD
# =====================================================

def perform_build(
    build,
    build_dir
):

    required = [
        MOD_FILE,
        SQL_FILE,
        JNI_FILE,
    ]

    for file in required:

        if not file.exists():

            raise RuntimeError(
                f"Не найден файл: {file.name}"
            )

    prepared = prepare_mod(
        build,
        build_dir
    )

    lib_file = build_client(
        build,
        build_dir
    )

    ftp_result = None

    if build.get("ftp"):

        ftp_result = upload_ftp(
            build["ftp"],
            prepared["mod_dir"]
        )

    return {
        "sql": prepared["sql_path"],
        "lib": lib_file,
        "ftp": ftp_result
    }


# =====================================================
# CREATE BUILD
# =====================================================

async def create_build(
    update,
    context,
    user_id,
    build
):

    build_id = (
        f"{user_id}_"
        f"{int(time.time())}"
    )

    build_dir = (
        BASE_DIR /
        str(build_id)
    )

    build_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    data = load_data()

    data["builds"][
        str(build_id)
    ] = build

    save_data(data)

    status_message = await context.bot.send_message(
        chat_id=user_id,
        text=(
            "⏳ <b>Начинаю сборку...</b>\n\n"
            "1️⃣ Подготавливаю мод\n"
            "2️⃣ Генерирую SQL\n"
            "3️⃣ Собираю JNI через Gradle\n"
            "4️⃣ Получаю libsvoyak.so\n"
            "5️⃣ Загружаю мод на FTP\n\n"
            "⏱ Это может занять некоторое время."
        ),
        parse_mode="HTML"
    )

    loop = asyncio.get_running_loop()

    try:

        result = await loop.run_in_executor(
            None,
            perform_build,
            build,
            build_dir
        )

        # =================================================
        # LIB
        # =================================================

        if (
            result["lib"]
            and result["lib"].exists()
        ):

            with open(
                result["lib"],
                "rb"
            ) as file:

                await context.bot.send_document(
                    chat_id=user_id,
                    document=file,
                    caption=(
                        "✅ <b>JNI библиотека готова!</b>\n\n"
                        "📦 <code>libsvoyak.so</code>\n"
                        "🏗 ABI: <code>arm64-v8a</code>\n"
                        "🧩 NDK: <code>r25c</code>"
                    ),
                    parse_mode="HTML"
                )

        # =================================================
        # SQL
        # =================================================

        if (
            result["sql"]
            and result["sql"].exists()
        ):

            with open(
                result["sql"],
                "rb"
            ) as file:

                await context.bot.send_document(
                    chat_id=user_id,
                    document=file,
                    caption=(
                        "🗄 <b>svoyak.sql</b>\n\n"
                        "Этот файл <b>НЕ загружался на FTP</b>.\n"
                        "Импортируй его вручную в MySQL."
                    ),
                    parse_mode="HTML"
                )

        # =================================================
        # FTP
        # =================================================

        if result["ftp"]:

            ftp_text = (
                "\n\n"
                "📁 <b>FTP:</b> мод загружен в корень.\n"
                f"🗑 Старых объектов заменено: "
                f"<b>{result['ftp']['deleted']}</b>\n"
                f"📤 Файлов загружено: "
                f"<b>{result['ftp']['uploaded']}</b>\n"
                "🗄 SQL на FTP не загружался."
            )

        else:

            ftp_text = (
                "\n\n"
                "📁 FTP: пропущен."
            )

        # =================================================
        # СОХРАНЕНИЕ ПРОЕКТА
        # =================================================

        user = get_user(
            data,
            user_id
        )

        user["projects"].append({
            "name": build["project_name"],
            "server": build["server"],
            "owner": build["owner"],
            "build_id": build_id,
            "created_at": int(time.time())
        })

        user["free_build"] = True

        save_data(data)

        await status_message.edit_text(
            (
                "🎉 <b>Сборка завершена!</b>\n\n"
                f"🌐 Сервер: "
                f"<code>{build['server']}</code>\n"
                f"📱 Проект: "
                f"<b>{build['project_name']}</b>\n"
                f"👤 Владелец: "
                f"<b>{build['owner']}</b>\n\n"
                "📦 JNI: "
                "<code>libsvoyak.so</code>\n"
                "🏗 ABI: "
                "<code>arm64-v8a</code>\n"
                "🧩 NDK: "
                "<code>r25c</code>\n"
                "🗄 SQL: готов и отправлен отдельно."
                + ftp_text
            ),
            parse_mode="HTML"
        )

    except Exception as e:

        await status_message.edit_text(
            (
                "❌ <b>Ошибка сборки</b>\n\n"
                f"<code>{str(e)[:7000]}</code>"
            ),
            parse_mode="HTML"
        )


# =====================================================
# ADMIN UPLOAD
# =====================================================

async def admin_upload_document(
    update,
    context
):

    if update.effective_user.id != ADMIN_ID:
        return

    document = update.message.document

    if not document:
        return

    mode = context.user_data.get(
        "admin_upload_mode"
    )

    if not mode:
        return

    filename = (
        document.file_name or ""
    )

    # -------------------------------------------------
    # MOD
    # -------------------------------------------------

    if mode == "mod":

        if not filename.lower().endswith(
            ".zip"
        ):

            await update.message.reply_text(
                "❌ Мод должен быть ZIP-архивом."
            )

            return

        target = MOD_FILE

    # -------------------------------------------------
    # SQL
    # -------------------------------------------------

    elif mode == "sql":

        if not filename.lower().endswith(
            ".sql"
        ):

            await update.message.reply_text(
                "❌ Нужен SQL-файл."
            )

            return

        target = SQL_FILE

    # -------------------------------------------------
    # JNI
    # -------------------------------------------------

    elif mode == "jni":

        if not filename.lower().endswith(
            ".zip"
        ):

            await update.message.reply_text(
                "❌ JNI-проект должен быть ZIP-архивом."
            )

            return

        target = JNI_FILE

    else:
        return

    try:

        file = await document.get_file()

        await file.download_to_drive(
            custom_path=str(target)
        )

        context.user_data.pop(
            "admin_upload_mode",
            None
        )

        await update.message.reply_text(
            (
                "✅ <b>Файл успешно загружен!</b>\n\n"
                f"📦 {target.name}"
            ),
            parse_mode="HTML",
            reply_markup=admin_menu()
        )

    except Exception as e:

        await update.message.reply_text(
            (
                "❌ Ошибка загрузки:\n"
                f"<code>{str(e)}</code>"
            ),
            parse_mode="HTML"
        )


# =====================================================
# ADMIN USERS
# =====================================================

async def admin_users(
    update,
    context
):

    if update.effective_user.id != ADMIN_ID:
        return

    data = load_data()

    users = data.get(
        "users",
        {}
    )

    if not users:

        text = (
            "👥 <b>Пользователи</b>\n\n"
            "Пользователей пока нет."
        )

    else:

        lines = [
            f"👥 <b>Пользователи:</b> {len(users)}\n"
        ]

        for user_id, user in list(
            users.items()
        )[:30]:

            status = (
                "🚫"
                if user.get("blocked")
                else "✅"
            )

            balance = user.get(
                "balance",
                0
            )

            projects_count = len(
                user.get(
                    "projects",
                    []
                )
            )

            lines.append(
                f"{status} <code>{user_id}</code> "
                f"💰 {balance} "
                f"📂 {projects_count}"
            )

        if len(users) > 30:

            lines.append(
                "\nПоказаны первые 30."
            )

        text = "\n".join(lines)

    await update.callback_query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=back_menu("admin_panel")
    )


# =====================================================
# ADMIN STATS
# =====================================================

async def admin_stats(
    update,
    context
):

    if update.effective_user.id != ADMIN_ID:
        return

    data = load_data()

    users = data.get(
        "users",
        {}
    )

    builds = data.get(
        "builds",
        {}
    )

    total_projects = 0
    blocked = 0
    balance = 0

    for user in users.values():

        total_projects += len(
            user.get(
                "projects",
                []
            )
        )

        balance += int(
            user.get(
                "balance",
                0
            )
        )

        if user.get("blocked"):
            blocked += 1

    text = (
        "📊 <b>Статистика SVOYAK</b>\n\n"
        f"👥 Пользователей: <b>{len(users)}</b>\n"
        f"🚫 Заблокировано: <b>{blocked}</b>\n"
        f"🏗 Сборок: <b>{len(builds)}</b>\n"
        f"📂 Проектов: <b>{total_projects}</b>\n"
        f"💰 Баланс пользователей: <b>{balance}</b>\n\n"
        f"📦 Мод: "
        f"{'✅' if MOD_FILE.exists() else '❌'}\n"
        f"🗄 SQL: "
        f"{'✅' if SQL_FILE.exists() else '❌'}\n"
        f"🧩 JNI: "
        f"{'✅' if JNI_FILE.exists() else '❌'}"
    )

    await update.callback_query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=back_menu("admin_panel")
    )


# =====================================================
# ADMIN POINTS
# =====================================================

async def admin_points(
    update,
    context
):

    if update.effective_user.id != ADMIN_ID:
        return

    context.user_data[
        "admin_action"
    ] = "points"

    await update.callback_query.edit_message_text(
        "💰 <b>Управление очками</b>\n\n"
        "Отправь:\n"
        "<code>ID КОЛИЧЕСТВО</code>\n\n"
        "Например:\n"
        "<code>123456789 500</code>\n\n"
        "Чтобы снять очки, укажи отрицательное число:\n"
        "<code>123456789 -100</code>",
        parse_mode="HTML",
        reply_markup=back_menu("admin_panel")
    )


# =====================================================
# ADMIN BROADCAST
# =====================================================

async def admin_broadcast(
    update,
    context
):

    if update.effective_user.id != ADMIN_ID:
        return

    context.user_data[
        "admin_action"
    ] = "broadcast"

    await update.callback_query.edit_message_text(
        "📢 <b>Рассылка</b>\n\n"
        "Отправь текст сообщения.\n\n"
        "Сообщение будет отправлено всем пользователям.",
        parse_mode="HTML",
        reply_markup=back_menu("admin_panel")
    )


# =====================================================
# ADMIN TEXT ACTIONS
# =====================================================

async def admin_text_handler(
    update,
    context
):

    if update.effective_user.id != ADMIN_ID:
        return

    action = context.user_data.get(
        "admin_action"
    )

    if not action:
        return

    value = update.message.text.strip()

    # -------------------------------------------------
    # ОЧКИ
    # -------------------------------------------------

    if action == "points":

        parts = value.split()

        if len(parts) != 2:

            await update.message.reply_text(
                "❌ Формат:\n"
                "<code>ID КОЛИЧЕСТВО</code>",
                parse_mode="HTML"
            )

            return

        try:

            target_id = int(parts[0])
            amount = int(parts[1])

        except ValueError:

            await update.message.reply_text(
                "❌ ID и количество должны быть числами."
            )

            return

        data = load_data()

        user = get_user(
            data,
            target_id
        )

        user["balance"] += amount

        if user["balance"] < 0:
            user["balance"] = 0

        save_data(data)

        context.user_data.pop(
            "admin_action",
            None
        )

        await update.message.reply_text(
            (
                "✅ <b>Баланс изменён.</b>\n\n"
                f"👤 ID: <code>{target_id}</code>\n"
                f"💰 Баланс: <b>{user['balance']}</b>"
            ),
            parse_mode="HTML",
            reply_markup=admin_menu()
        )

        return

    # -------------------------------------------------
    # РАССЫЛКА
    # -------------------------------------------------

    if action == "broadcast":

        data = load_data()

        users = data.get(
            "users",
            {}
        )

        sent = 0
        failed = 0

        status = await update.message.reply_text(
            "📢 Начинаю рассылку..."
        )

        for user_id, user in users.items():

            if user.get("blocked"):
                continue

            try:

                await context.bot.send_message(
                    chat_id=int(user_id),
                    text=value
                )

                sent += 1

                await asyncio.sleep(
                    0.05
                )

            except Exception:

                failed += 1

        context.user_data.pop(
            "admin_action",
            None
        )

        await status.edit_text(
            (
                "📢 <b>Рассылка завершена.</b>\n\n"
                f"✅ Отправлено: <b>{sent}</b>\n"
                f"❌ Ошибок: <b>{failed}</b>"
            ),
            parse_mode="HTML",
            reply_markup=admin_menu()
        )


# =====================================================
# INVOICE
# =====================================================

async def send_project_invoice(
    update,
    context,
    product
):

    prices = {
        "pro": 499,
        "ultimate": 999
    }

    titles = {
        "pro": "SVOYAK PRO",
        "ultimate": "SVOYAK ULTIMATE"
    }

    if product not in prices:
        return

    provider_token = os.getenv(
        "PAYMENT_PROVIDER_TOKEN",
        ""
    )

    if not provider_token:

        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=(
                "❌ Оплата пока не настроена.\n\n"
                "Администратору нужно добавить "
                "PAYMENT_PROVIDER_TOKEN."
            )
        )

        return

    await context.bot.send_invoice(
        chat_id=update.effective_user.id,
        title=titles[product],
        description="Покупка тарифа SVOYAK",
        payload=product,
        provider_token=provider_token,
        currency="RUB",
        prices=[
            LabeledPrice(
                titles[product],
                prices[product]
            )
        ]
    )


# =====================================================
# PRECHECKOUT
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
# SUCCESS PAYMENT
# =====================================================

async def successful_payment(
    update,
    context
):

    user = update.effective_user

    payment = (
        update.message.successful_payment
    )

    product = payment.invoice_payload

    data = load_data()

    db_user = get_user(
        data,
        user.id
    )

    db_user["has_purchased"] = True

    # -------------------------------------------------
    # РЕФЕРАЛЬНЫЕ 15%
    # -------------------------------------------------

    referrer_id = db_user.get(
        "referrer"
    )

    if referrer_id:

        try:

            referrer = get_user(
                data,
                int(referrer_id)
            )

            amount = payment.total_amount

            profit = int(
                amount * 0.15
            )

            referrer["balance"] += profit
            referrer["total_profit"] += profit
            referrer["monthly_profit"] += profit
            referrer["weekly_profit"] += profit
            referrer["today_profit"] += profit

        except Exception:
            pass

    save_data(data)

    await update.message.reply_text(
        (
            "🎉 <b>Оплата прошла успешно!</b>\n\n"
            f"📦 Тариф: <b>{product.upper()}</b>\n\n"
            "Спасибо за покупку!"
        ),
        parse_mode="HTML",
        reply_markup=main_menu(user.id)
    )


# =====================================================
# BUTTONS
# =====================================================

async def buttons(
    update,
    context
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id
    data = query.data

    # =================================================
    # MAIN
    # =================================================

    if data == "main_menu":

        await query.edit_message_text(
            "🤖 <b>SVOYAK</b>\n\n"
            "Главное меню:",
            parse_mode="HTML",
            reply_markup=main_menu(user_id)
        )

    # =================================================
    # SHOP
    # =================================================

    elif data == "shop":

        await query.edit_message_text(
            "🛒 <b>Магазин</b>\n\n"
            "Выбери тариф:",
            parse_mode="HTML",
            reply_markup=shop_menu()
        )

    elif data == "pro":

        await query.edit_message_text(
            "⭐ <b>SVOYAK PRO</b>\n\n"
            "Расширенные возможности проекта.",
            parse_mode="HTML",
            reply_markup=pro_menu()
        )

    elif data == "ultimate":

        await query.edit_message_text(
            "💎 <b>SVOYAK ULTIMATE</b>\n\n"
            "Максимальный набор возможностей.",
            parse_mode="HTML",
            reply_markup=ultimate_menu()
        )

    elif data == "compare":

        await query.edit_message_text(
            "📊 <b>Сравнение тарифов</b>\n\n"
            "⭐ PRO — расширенные функции\n"
            "💎 ULTIMATE — полный набор функций",
            parse_mode="HTML",
            reply_markup=compare_menu()
        )

    elif data == "buy_pro":

        await send_project_invoice(
            update,
            context,
            "pro"
        )

    elif data == "buy_ultimate":

        await send_project_invoice(
            update,
            context,
            "ultimate"
        )

    # =================================================
    # FREE BUILD
    # =================================================

    elif data == "free_build":

        await free_build_start(
            update,
            context
        )

    # =================================================
    # BUILD
    # =================================================

    elif data == "build":

        await query.edit_message_text(
            "⚙️ <b>Сборка</b>\n\n"
            "Для сборки используй бесплатный проект "
            "или купленный тариф.",
            parse_mode="HTML",
            reply_markup=back_menu()
        )

    # =================================================
    # PROJECTS
    # =================================================

    elif data == "projects":

        await projects(
            update,
            context
        )

    # =================================================
    # SUPPORT
    # =================================================

    elif data == "support":

        await support(
            update,
            context
        )

    # =================================================
    # PARTNER
    # =================================================

    elif data == "partner":

        await partner(
            update,
            context
        )

    # =================================================
    # ADMIN PANEL
    # =================================================

    elif data == "admin_panel":

        if user_id != ADMIN_ID:
            return

        await query.edit_message_text(
            "👑 <b>Админ-панель</b>",
            parse_mode="HTML",
            reply_markup=admin_menu()
        )

    # =================================================
    # ADMIN ACTIONS
    # =================================================

    elif data.startswith("admin_"):

        if user_id != ADMIN_ID:
            return

        if data == "admin_mod":

            context.user_data[
                "admin_upload_mode"
            ] = "mod"

            await query.edit_message_text(
                "📦 <b>Загрузка мода</b>\n\n"
                "Отправь ZIP-архив с модом.",
                parse_mode="HTML",
                reply_markup=back_menu(
                    "admin_panel"
                )
            )

        elif data == "admin_sql":

            context.user_data[
                "admin_upload_mode"
            ] = "sql"

            await query.edit_message_text(
                "🗄 <b>Загрузка SQL</b>\n\n"
                "Отправь файл <code>.sql</code>.",
                parse_mode="HTML",
                reply_markup=back_menu(
                    "admin_panel"
                )
            )

        elif data == "admin_jni":

            context.user_data[
                "admin_upload_mode"
            ] = "jni"

            await query.edit_message_text(
                "🧩 <b>Загрузка JNI-проекта</b>\n\n"
                "Отправь ZIP-архив.\n\n"
                "Внутри должен находиться "
                "<code>gradlew</code>.",
                parse_mode="HTML",
                reply_markup=back_menu(
                    "admin_panel"
                )
            )

        elif data == "admin_status":

            mod_status = (
                "✅ Загружен"
                if MOD_FILE.exists()
                else "❌ Нет"
            )

            sql_status = (
                "✅ Загружен"
                if SQL_FILE.exists()
                else "❌ Нет"
            )

            jni_status = (
                "✅ Загружен"
                if JNI_FILE.exists()
                else "❌ Нет"
            )

            await query.edit_message_text(
                (
                    "📋 <b>Статус файлов</b>\n\n"
                    f"📦 Мод: {mod_status}\n"
                    f"🗄 SQL: {sql_status}\n"
                    f"🧩 JNI: {jni_status}\n\n"
                    "⚙️ Сборка: Gradle\n"
                    "📱 ABI: arm64-v8a\n"
                    "🧩 NDK: r25c\n"
                    "🚫 build_client.sh: не используется\n"
                    "🚫 SQL на FTP: не загружается"
                ),
                parse_mode="HTML",
                reply_markup=back_menu(
                    "admin_panel"
                )
            )

        elif data == "admin_users":

            await admin_users(
                update,
                context
            )

        elif data == "admin_stats":

            await admin_stats(
                update,
                context
            )

        elif data == "admin_points":

            await admin_points(
                update,
                context
            )

        elif data == "admin_broadcast":

            await admin_broadcast(
                update,
                context
            )


# =====================================================
# RUN
# =====================================================

def run():

    if not TOKEN:

        raise RuntimeError(
            "Не задан BOT_TOKEN."
        )

    # Health server
    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    # =================================================
    # КОМАНДЫ
    # =================================================

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CommandHandler(
            "admin",
            admin_command
        )
    )

    # =================================================
    # АДМИНСКИЕ ТЕКСТОВЫЕ ДЕЙСТВИЯ
    # =================================================

    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            admin_text_handler
        ),
        group=0
    )

    # =================================================
    # ДОКУМЕНТЫ АДМИНКИ
    # =================================================

    application.add_handler(
        MessageHandler(
            filters.Document.ALL,
            admin_upload_document
        )
    )

    # =================================================
    # FREE BUILD
    # =================================================

    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            free_build_message
        ),
        group=1
    )

    # =================================================
    # КНОПКИ
    # =================================================

    application.add_handler(
        CallbackQueryHandler(
            buttons
        )
    )

    # =================================================
    # ПЛАТЕЖИ
    # =================================================

    application.add_handler(
        PreCheckoutQueryHandler(
            precheckout_callback
        )
    )

    application.add_handler(
        MessageHandler(
            filters.SUCCESSFUL_PAYMENT,
            successful_payment
        )
    )

    print(
        "SVOYAK BOT started..."
    )

    application.run_polling(
        drop_pending_updates=True
    )


# =====================================================
# START
# =====================================================

if __name__ == "__main__":
    run()
