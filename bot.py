from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo,
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
        [KeyboardButton("Inline buttons"), KeyboardButton("Help")],
        [
            KeyboardButton("Send contact", request_contact=True),
            KeyboardButton("Send location", request_location=True),
        ],
        [KeyboardButton("Open web app", web_app=WebAppInfo(url="https://example.com"))],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Choose an option:", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Inline buttons":
        keyboard = [
            [
                InlineKeyboardButton("Option 1", callback_data="opt1"),
                InlineKeyboardButton("Option 2", callback_data="opt2"),
            ],
            [InlineKeyboardButton("Open GitHub", url="https://github.com")],
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Inline buttons:", reply_markup=markup)
    elif text == "Help":
        await update.message.reply_text(
            "This is a demo bot showcasing Telegram UI features."
        )
    else:
        await update.message.reply_text("Use the keyboard to select an option.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=f"Selected: {query.data}")

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.run_polling()

if __name__ == "__main__":
    main()
