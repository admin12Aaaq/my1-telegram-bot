import telebot
import sqlite3
import uuid
import os
import qrcode
from telebot import types

# ==================== CONFIGURATION (تنظیمات اختصاصی شما) ====================
BOT_TOKEN = "8744600190:AAHOSJlAPBfGbwSKI7yR-QSSUlrMcKKGIyI"
ADMIN_ID = 2010636810  

CARD_NUMBER = "6037-7012-1103-5784"
CARD_HOLDER = "ابوالفضل سلطانی"

SUPPORT_USERNAME = "K2_XAEA"  # آیدی پشتیبانی جدید شما
# ==============================================================================

bot = telebot.TeleBot(BOT_TOKEN)

# متغیر برای مدیریت وضعیت ادمین در زمان تحویل کانفیگ
waiting_for_admin = {}

def init_db():
    conn = sqlite3.connect("telebot_shop.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY, user_id INTEGER, volume INTEGER, days INTEGER, status TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, config_text TEXT, sub_link TEXT
        )
    """)
    conn.commit()
    conn.close()

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🛒 خرید کانفیگ", "🎁 دریافت اکانت تست")
    markup.row("📊 سرویس‌های من", "📞 پشتیبانی")
    return markup

@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.send_message(message.chat.id, "سلام! به ربات فروش کانفیگ خوش آمدید. لطفاً یکی از گزینه‌ها را انتخاب کنید:", reply_markup=main_menu())

# ==================== TEST ACCOUNT SECTION ====================
@bot.message_handler(func=lambda msg: msg.text == "🎁 دریافت اکانت تست")
def test_request_handler(message):
    user_id = message.chat.id
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تایید و ارسال تست", callback_data=f"test_approve_{user_id}"),
        types.InlineKeyboardButton("❌ رد درخواست", callback_data=f"test_reject_{user_id}")
    )
    
    bot.send_message(ADMIN_ID, f"🔔 درخواست اکانت تست جدید!\n👤 کاربر: {message.from_user.first_name}\n🆔 آیدی: `{user_id}`", reply_markup=markup, parse_mode="Markdown")
    bot.send_message(user_id, "⏳ درخواست اکانت تست شما برای ادمین ارسال شد. به محض تایید، کانفیگ براتون فرستاده میشه.")

# ==================== BUY CONFIG SECTION ====================
@bot.message_handler(func=lambda msg: msg.text == "🛒 خرید کانفیگ")
def buy_config_start(message):
    bot.send_message(message.chat.id, "✍️ لطفاً حجم درخواستی خود را به **گیگابایت** وارد کنید:\n(مثلاً فقط عدد انگلیسی بفرستید: 20 یا 50 یا 100)")

@bot.message_handler(func=lambda msg: msg.text and msg.text.isdigit() and not msg.chat.id == ADMIN_ID)
def process_user_volume(message):
    user_id = message.chat.id
    volume = int(message.text)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📅 ۳۰ روزه (۱ ماهه)", callback_data=f"days_30_{volume}"))
    markup.add(types.InlineKeyboardButton("📅 ۶۰ روزه (۲ ماهه)", callback_data=f"days_60_{volume}"))
    markup.add(types.InlineKeyboardButton("📅 ۹۰ روزه (۳ ماهه)", callback_data=f"days_90_{volume}"))
    
    bot.send_message(user_id, f"📅 حجم انتخاب شده: {volume} گیگابایت\n\nحالا مدت زمان اکانت را انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("days_"))
def process_days_selection(call):
    user_id = call.message.chat.id
    data = call.data.split("_")
    days = int(data[1])
    volume = int(data[2])
    order_id = str(uuid.uuid4())[:8]
    
    conn = sqlite3.connect("telebot_shop.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", (order_id, user_id, volume, days, "PENDING"))
    conn.commit()
    conn.close()
    
    msg_text = (
        f"📋 **جزئیات سفارش شما:**\n"
        f"🆔 شماره سفارش: `{order_id}`\n"
        f"📊 حجم درخواستی: {volume} گیگابایت\n"
        f"📅 مدت زمان: {days} روزه\n\n"
        f"لطفاً مبلغ معادل را به شماره کارت زیر واریز نمایید:\n"
        f"💳 `{CARD_NUMBER}`\n"
        f"👤 به نام: {CARD_HOLDER}\n\n"
        f"⚠️ **مهم:** پس از واریز، عکس فیش واریزی خود را ارسال کنید تا بررسی شود."
    )
    bot.edit_message_text(msg_text, chat_id=user_id, message_id=call.message.message_id, parse_mode="Markdown")

# مدیریت هوشمند دریافت عکس فیش واریزی
@bot.message_handler(content_types=['photo'])
def handle_receipt_photo(message):
    user_id = message.chat.id
    
    conn = sqlite3.connect("telebot_shop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, volume, days FROM orders WHERE user_id=? AND status='PENDING' ORDER BY rowid DESC LIMIT 1", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        bot.send_message(user_id, "❌ شما در حال حاضر هیچ سفارش ثبت شده یا معلقی ندارید. ابتدا دکمه خرید کانفیگ را بزنید.")
        return
        
    order_id, volume, days = row[0], row[1], row[2]
    
    bot.forward_message(ADMIN_ID, user_id, message.message_id)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تایید فیش و ساخت کانفیگ", callback_data=f"order_approve_{order_id}_{user_id}"),
        types.InlineKeyboardButton("❌ رد کردن فیش", callback_data=f"order_reject_{order_id}_{user_id}")
    )
    
    bot.send_message(
        ADMIN_ID, 
        f"🔔 **فیش جدید دریافت شد!**\n\n"
        f"👤 فرستنده: {message.from_user.first_name}\n"
        f"🆔 شماره سفارش: `{order_id}`\n"
        f"📊 مشخصات: {volume} گیگ - {days} روزه", 
        reply_markup=markup, 
        parse_mode="Markdown"
    )
    bot.send_message(user_id, "⏳ فیش واریزی شما با موفقیت برای ادمین ارسال شد. پس از تایید، سرویس شما تحویل داده می‌شود.")

# ==================== ADMIN ACTIONS & TEXT DELIVERY ====================
@bot.callback_query_handler(func=lambda call: call.data.startswith(("order_", "test_")))
def handle_admin_callbacks(call):
    global waiting_for_admin
    if call.from_user.id != ADMIN_ID:
        return
        
    data = call.data.split("_")
    
    if data[0] == "order":
        action, order_id, user_id = data[1], data[2], int(data[3])
        if action == "approve":
            waiting_for_admin[ADMIN_ID] = {"user_id": user_id, "order_id": order_id, "step": "waiting_for_config"}
            bot.edit_message_text(f"سفارش `{order_id}` تایید شد.\n\n👇 ابتدا **متن خود کانفیگ** را بفرستید:", chat_id=ADMIN_ID, message_id=call.message.message_id)
        elif action == "reject":
            conn = sqlite3.connect("telebot_shop.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE orders SET status='REJECTED' WHERE id=?", (order_id,))
            conn.commit()
            conn.close()
            bot.send_message(user_id, "❌ فیش واریزی شما توسط ادمین رد شد.")
            bot.edit_message_text("سفارش رد شد.", chat_id=ADMIN_ID, message_id=call.message.message_id)
            
    elif data[0] == "test":
        action, user_id = data[1], int(data[2])
        if action == "approve":
            waiting_for_admin[ADMIN_ID] = {"user_id": user_id, "order_id": "TEST_ACC", "step": "waiting_for_config"}
            bot.edit_message_text("درخواست تست تایید شد.\n\n👇 ابتدا **متن کانفیگ تست** را بفرستید:", chat_id=ADMIN_ID, message_id=call.message.message_id)
        elif action == "reject":
            bot.send_message(user_id, "❌ درخواست اکانت تست شما رد شد.")
            bot.edit_message_text("درخواست تست رد شد.", chat_id=ADMIN_ID, message_id=call.message.message_id)

@bot.message_handler(func=lambda msg: msg.chat.id == ADMIN_ID and ADMIN_ID in waiting_for_admin)
def handle_admin_inputs(message):
    session = waiting_for_admin[ADMIN_ID]
    target_user = session["user_id"]
    order_id = session["order_id"]
    
    if session["step"] == "waiting_for_config":
        waiting_for_admin[ADMIN_ID]["config_text"] = message.text
        waiting_for_admin[ADMIN_ID]["step"] = "waiting_for_sub"
        bot.send_message(ADMIN_ID, "🔗 عالیه. حالا **لینک ساب (Subscription Link)** را بفرستید:")
        
    elif session["step"] == "waiting_for_sub":
        sub_link = message.text
        config_text = session["config_text"]
        
        qr_path = f"qr_{target_user}.png"
        img = qrcode.make(sub_link)
        img.save(qr_path)
        
        conn = sqlite3.connect("telebot_shop.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO services (user_id, config_text, sub_link) VALUES (?, ?, ?)", (target_user, config_text, sub_link))
        if order_id != "TEST_ACC":
            cursor.execute("UPDATE orders SET status='APPROVED' WHERE id=?", (order_id,))
        conn.commit()
        conn.close()
        
        success_msg = f"🎉 سرویس شما با موفقیت تحویل داده شد!\n\n🚀 **کانفیگ اختصاصی:**\n`{config_text}`\n\n🔗 **لینک ساب:**\n`{sub_link}`\n\n👇 همچنین می‌توانید QR کد زیر را اسکن کنید:"
        with open(qr_path, 'rb') as photo:
            bot.send_photo(target_user, photo, caption=success_msg, parse_mode="Markdown")
            
        os.remove(qr_path)
        del waiting_for_admin[ADMIN_ID]
        bot.send_message(ADMIN_ID, "✅ سرویس با موفقیت برای کاربر ارسال شد.")

# ==================== SERVICES & SUPPORT ====================
@bot.message_handler(func=lambda msg: msg.text == "📊 سرویس‌های من")
def my_services_handler(message):
    conn = sqlite3.connect("telebot_shop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT config_text, sub_link FROM services WHERE user_id=?", (message.chat.id,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        bot.send_message(message.chat.id, "📭 شما در حال حاضر هیچ سرویس فعالی ندارید.")
        return
        
    bot.send_message(message.chat.id, f"📊 شما دارای {len(rows)} سرویس فعال هستید. در حال ارسال مشخصات...")
    
    for row in rows:
        config, sub = row[0], row[1]
        qr_path = f"qr_view_{message.chat.id}.png"
        img = qrcode.make(sub)
        img.save(qr_path)
        
        with open(qr_path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=f"🚀 **کانفیگ:**\n`{config}`\n\n🔗 **لینک ساب:**\n`{sub}`", parse_mode="Markdown")
        os.remove(qr_path)

@bot.message_handler(func=lambda msg: msg.text == "📞 پشتیبانی")
def support_handler(message):
    bot.send_message(message.chat.id, f"📞 جهت ارتباط با پشتیبانی، تمدید یا طرح سوالات به آیدی زیر پیام دهید:\n\n👉 @{SUPPORT_USERNAME}")

if __name__ == "__main__":
    init_db()
    print("Telebot Manual Bot Started Successfully.")
    bot.infinity_polling()
