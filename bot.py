import asyncio
import sqlite3
from datetime import datetime
from telegram import Update, LabeledPrice
from telegram.ext import Application, CommandHandler, MessageHandler, filters, PreCheckoutQueryHandler, ContextTypes

# متغيرات ثابتة
TOKEN = "8492758125:AAHlVlTJsEKalJOxjAJDmHy7vZ7cFRjpQN8"  # استبدل بتوكن البوت الخاص بك من BotFather
ADMIN_ID = 793878365  # استبدل بمعرف الإدمن (user_id)
PRICE_STARS = 0  # سعر الاشتراك بالنجوم (يمكن تغييره)

# إنشاء قاعدة البيانات SQLite وجدول المستخدمين إذا لم يكن موجوداً
def init_db():
    conn = sqlite3.connect('subscribers.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            stars_paid INTEGER DEFAULT 0,
            subscription_status TEXT DEFAULT 'inactive',
            subscription_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

# دالة لإضافة أو تحديث مستخدم في قاعدة البيانات
def add_or_update_user(user_id, username=None, stars_paid=0, status='inactive', date=None):
    conn = sqlite3.connect('subscribers.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, username, stars_paid, subscription_status, subscription_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, stars_paid, status, date))
    conn.commit()
    conn.close()

# دالة للحصول على بيانات مستخدم
def get_user(user_id):
    conn = sqlite3.connect('subscribers.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

# دالة للحصول على جميع المشتركين (للإدمن فقط)
def get_all_subscribers():
    conn = sqlite3.connect('subscribers.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, stars_paid, subscription_status, subscription_date FROM users WHERE subscription_status = "active"')
    subscribers = cursor.fetchall()
    conn.close()
    return subscribers

# handler للأمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    # إضافة المستخدم إلى قاعدة البيانات إذا لم يكن موجوداً
    add_or_update_user(user.id, user.username)
    await update.message.reply_text(
        f"مرحبا {user.mention_html()}!\n"
        "هذا بوت اشتراك مدفوع باستخدام Telegram Stars.\n"
        "استخدم /buy لشراء اشتراك، أو /status لمعرفة حالة اشتراكك.",
        parse_mode='HTML'
    )

# handler للأمر /buy
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    # إرسال فاتورة الدفع باستخدام النجوم
    await context.bot.send_invoice(
        chat_id=user.id,
        title="اشتراك في البوت",
        description="اشتراك شهري للوصول إلى الميزات المتقدمة.",
        payload=f"subscription_{user.id}",  # payload فريد للتعرف على الدفع
        provider_token="",  # فارغ للدفع بالنجوم
        currency="XTR",  # XTR للنجوم
        prices=[LabeledPrice("اشتراك", PRICE_STARS)],  # السعر بالنجوم
        start_parameter="subscription"  # معلمة اختيارية
    )

# handler للأمر /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_data = get_user(user.id)
    if user_data:
        status = user_data[3]  # subscription_status
        date = user_data[4]  # subscription_date
        stars = user_data[2]  # stars_paid
        await update.message.reply_text(
            f"حالة اشتراكك: {status}\n"
            f"النجوم المدفوعة: {stars}\n"
            f"تاريخ الاشتراك: {date if date else 'غير محدد'}"
        )
    else:
        await update.message.reply_text("لم يتم العثور على بياناتك. جرب /start أولاً.")

# handler للأمر /subscribers (للإدمن فقط)
async def subscribers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.id == ADMIN_ID:
        subs = get_all_subscribers()
        if subs:
            message = "قائمة المشتركين النشطين:\n"
            for sub in subs:
                message += f"ID: {sub[0]}, Username: @{sub[1]}, Stars: {sub[2]}, Date: {sub[3]}\n"
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("لا يوجد مشتركين نشطين.")
    else:
        await update.message.reply_text("هذا الأمر مخصص للإدمن فقط.")

# handler للتحقق من الدفع قبل الإتمام (pre-checkout)
async def pre_checkout_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    # قبول الدفع دائماً (يمكن إضافة تحقق إضافي هنا)
    await query.answer(ok=True)

# handler للدفع الناجح
async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    payment = update.message.successful_payment
    user_id = update.effective_user.id
    # التحقق من payload للتأكد من أنه دفع اشتراك
    if payment.invoice_payload.startswith("subscription_"):
        # تحديث بيانات المستخدم
        add_or_update_user(
            user_id=user_id,
            stars_paid=payment.total_amount,  # عدد النجوم المدفوعة
            status='active',
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        await update.message.reply_text("تم تفعيل اشتراكك بنجاح! شكراً لك.")

# الدالة الرئيسية لتشغيل البوت
def main() -> None:
    # تهيئة قاعدة البيانات
    init_db()
    
    # إنشاء التطبيق
    application = Application.builder().token(TOKEN).build()
    
    # إضافة handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("buy", buy))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("subscribers", subscribers))
    application.add_handler(PreCheckoutQueryHandler(pre_checkout_query))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    
    # تشغيل البوت
    application.run_polling()

if __name__ == '__main__':
    main()

