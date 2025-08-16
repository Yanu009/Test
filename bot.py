from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = "YOUR_BOT_TOKEN"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("Add Income"), KeyboardButton("Add Expense")],
        [KeyboardButton("View Summary"), KeyboardButton("Help")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "\U0001F4B0 *Finance Bot* — take control of your budget!",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_data = context.user_data

    awaiting = user_data.get("awaiting_amount")
    if awaiting:
        try:
            amount = float(text)
        except ValueError:
            await update.message.reply_text("Please send a valid number for the amount.")
            return
        action = user_data.pop("awaiting_amount")
        record = {
            "type": action["type"],
            "category": action["category"],
            "amount": amount,
        }
        user_data.setdefault("records", []).append(record)
        await update.message.reply_text(
            f"Recorded {action['type']} of {amount} in {action['category']}."
        )
        return

    if text == "Add Income":
        keyboard = [
            [
                InlineKeyboardButton("Salary", callback_data="income:Salary"),
                InlineKeyboardButton("Gift", callback_data="income:Gift"),
            ],
            [InlineKeyboardButton("Other", callback_data="income:Other")],
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Select income category:", reply_markup=markup)
    elif text == "Add Expense":
        keyboard = [
            [
                InlineKeyboardButton("Food", callback_data="expense:Food"),
                InlineKeyboardButton("Transport", callback_data="expense:Transport"),
            ],
            [InlineKeyboardButton("Other", callback_data="expense:Other")],
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Select expense category:", reply_markup=markup)
    elif text == "View Summary":
        records = user_data.get("records", [])
        income = sum(r["amount"] for r in records if r["type"] == "income")
        expense = sum(r["amount"] for r in records if r["type"] == "expense")
        balance = income - expense
        await update.message.reply_text(
            f"Income: {income}\nExpense: {expense}\nBalance: {balance}"
        )
    elif text == "Help":
        await update.message.reply_text(
            "Use the buttons to log income or expenses and view your summary."
        )
    else:
        await update.message.reply_text("Please choose an option from the keyboard.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action_type, category = query.data.split(":")
    context.user_data["awaiting_amount"] = {
        "type": action_type,
        "category": category,
    }
    await query.edit_message_text(
        f"{action_type.capitalize()} category: {category}\nNow send the amount."
    )

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.run_polling()

if __name__ == "__main__":
    main()
