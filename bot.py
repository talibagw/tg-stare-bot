import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    PreCheckoutQueryHandler
)

# ياخذ التوكن من Railway Environment Variables
TOKEN = os.getenv("TOKEN")

# /start
def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("⭐ اشتراك شهر (100 نجمة)", callback_data="pay")]
    ]
    update.message.reply_text(
        "👋 أهلاً بيك بالبوت\n\n"
        "🔐 هذا بوت اشتراك\n"
        "💳 الدفع يتم عن طريق نجوم تليگرام ⭐",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# الأزرار
def buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == "pay":
        prices = [
            LabeledPrice("اشتراك شهر", 100)  # 100 نجمة
        ]

        context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title="اشتراك VIP",
            description="اشتراك شهر كامل",
            payload="vip_month",
            provider_token="",      # فارغ لأن Stars
            currency="XTR",         # عملة النجوم
            prices=prices
        )

# تأكيد الدفع
def precheckout(update: Update, context: CallbackContext):
    update.pre_checkout_query.answer(ok=True)

# نجاح الدفع
def successful_payment(update: Update, context: CallbackContext):
    update.message.reply_text(
        "✅ تم الاشتراك بنجاح!\n"
        "⭐ شكراً لدعمك"
    )

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(buttons))
    dp.add_handler(PreCheckoutQueryHandler(precheckout))
    dp.add_handler(MessageHandler(Filters.successful_payment, successful_payment))

    updater.start_polling()
    updater.idle()

if name == "main":
    main()