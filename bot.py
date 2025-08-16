import csv
import datetime as dt
import json
import os
from pathlib import Path

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
    InputFile,
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Состояния диалога
MAIN, CATEGORY, AMOUNT, BUDGET = range(4)

# Файл для хранения данных
DATA_FILE = Path("data.json")


def load_data() -> dict:
    if DATA_FILE.exists():
        with DATA_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_data(data: dict) -> None:
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


USER_DATA = load_data()
TOKEN = "YOUR_BOT_TOKEN"


def main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        ["➕ Доход", "➖ Расход"],
        ["📊 Статистика", "💾 Экспорт CSV"],
        ["🎯 Бюджет"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Привет! Я помогу вести личные финансы. Выбирай действие:",
        reply_markup=main_keyboard(),
    )
    return MAIN


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user_id = str(update.effective_user.id)

    if text == "➕ Доход":
        context.user_data["type"] = "income"
        keyboard = [
            [
                InlineKeyboardButton("Зарплата", callback_data="Зарплата"),
                InlineKeyboardButton("Подарок", callback_data="Подарок"),
            ],
            [InlineKeyboardButton("Другое", callback_data="Другое")],
        ]
        await update.message.reply_text(
            "Выбери категорию дохода:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CATEGORY

    if text == "➖ Расход":
        context.user_data["type"] = "expense"
        keyboard = [
            [
                InlineKeyboardButton("Еда", callback_data="Еда"),
                InlineKeyboardButton("Транспорт", callback_data="Транспорт"),
            ],
            [
                InlineKeyboardButton("Развлечения", callback_data="Развлечения"),
                InlineKeyboardButton("Другое", callback_data="Другое"),
            ],
        ]
        await update.message.reply_text(
            "Выбери категорию расхода:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CATEGORY

    if text == "📊 Статистика":
        records = USER_DATA.get(user_id, {}).get("records", [])
        income = sum(r["amount"] for r in records if r["type"] == "income")
        expense = sum(r["amount"] for r in records if r["type"] == "expense")
        balance = income - expense
        budget = USER_DATA.get(user_id, {}).get("budget")
        reply = f"Доход: {income}\nРасход: {expense}\nБаланс: {balance}"
        if budget is not None:
            reply += f"\nБюджет: {budget}\nОстаток: {budget - expense}"
        await update.message.reply_text(reply)
        return MAIN

    if text == "💾 Экспорт CSV":
        records = USER_DATA.get(user_id, {}).get("records", [])
        if not records:
            await update.message.reply_text("Нет данных для экспорта.")
            return MAIN
        filename = f"finance_{user_id}.csv"
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["date", "type", "category", "amount"],
            )
            writer.writeheader()
            writer.writerows(records)
        await update.message.reply_document(InputFile(filename))
        os.remove(filename)
        return MAIN

    if text == "🎯 Бюджет":
        await update.message.reply_text(
            "Введи сумму месячного бюджета:", reply_markup=ReplyKeyboardRemove()
        )
        return BUDGET

    await update.message.reply_text("Пожалуйста, выбери действие кнопками ниже.")
    return MAIN


async def category_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["category"] = query.data
    await query.edit_message_text(
        f"Категория: {query.data}\nТеперь введи сумму.",
    )
    return AMOUNT


async def amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = str(update.effective_user.id)
    text = update.message.text.replace(",", ".")
    try:
        amount = float(text)
    except ValueError:
        await update.message.reply_text("Введите число.")
        return AMOUNT
    record = {
        "date": dt.date.today().isoformat(),
        "type": context.user_data["type"],
        "category": context.user_data["category"],
        "amount": amount,
    }
    USER_DATA.setdefault(user_id, {}).setdefault("records", []).append(record)
    save_data(USER_DATA)

    budget = USER_DATA.get(user_id, {}).get("budget")
    reply = "Сохранено!"
    if budget is not None:
        expenses = sum(
            r["amount"]
            for r in USER_DATA[user_id]["records"]
            if r["type"] == "expense"
        )
        if expenses > budget:
            reply += f"\n⚠️ Бюджет превышен на {expenses - budget}!"
    await update.message.reply_text(reply, reply_markup=main_keyboard())
    return MAIN


async def budget_set(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = str(update.effective_user.id)
    text = update.message.text.replace(",", ".")
    try:
        amount = float(text)
    except ValueError:
        await update.message.reply_text("Введите число.")
        return BUDGET
    USER_DATA.setdefault(user_id, {})["budget"] = amount
    save_data(USER_DATA)
    await update.message.reply_text(
        "Бюджет сохранён.", reply_markup=main_keyboard()
    )
    return MAIN


def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)],
            CATEGORY: [CallbackQueryHandler(category_chosen)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount_received)],
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, budget_set)],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(conv)
    application.run_polling()


if __name__ == "__main__":
    main()
