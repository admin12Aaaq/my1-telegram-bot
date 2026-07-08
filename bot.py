import telebot
from telebot import types
import time

# ----------------- تنظیمات اصلی و اختصاصی شما -----------------
API_TOKEN = '6810237517:AAH0Z_Ssc8wGkS5u_q47N0G4gY5MOfh7oO8'  # توکن ربات شما
ADMIN_ID = 6331901170  # آیدی عددی تلگرام شما (ابوالفضل)
CHANNEL_USERNAME = '@K2_XAEA'  # آیدی کانال شما جهت قفل اجباری

bot = telebot.TeleBot(API_TOKEN)

# ----------------- دیتابیس موقت در حافظه -----------------
users = set()  # ذخیره آیدی کاربران برای ارسال همگانی
sales_status = True  # وضعیت فروش کل ربات
test_status = True  # وضعیت تست رایگان

# آمار مالی
stats = {
    "today_income": 0,
    "month_income": 0,
    "total_sales_count": 0
}

# ذخیره موقت وضعیت ادمین و فیش‌ها
admin_state = {}
pending_receipts = {}

# ----------------- جدول قیمت‌های نهایی و تایید شده -----------------
PRICES = {
    "1gb": {"name": "1 گیگابایت", "1month": 100000, "2month": 160000, "3month": 240000},
    "2gb": {"name": "2 گیگابایت", "1month": 200000, "2month": 260000, "3month": 340000},
    "5gb": {"name": "5 گیگابایت", "1month": 300000, "2month": 360000, "3month": 440000},
    "10gb": {"name": "10 گیگابایت", "1month": 400000, "2month": 460000, "3month": 540000}
}

# ----------------- تابع بررسی عضویت اجباری کانال -----------------
def check_membership(user_id):
    try:
        chat_id = CHANNEL_USERNAME.replace('@', '')
        member = bot.get_chat_member(f"@{chat_id}", user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception:
        return True

# ----------------- دستور Start -----------------
@bot.message_handler(commands=['start'])
def welcome(message):
    user_id = message.from_user.id
    users.add(user_id)
    
    if not check_membership(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("ورود به کانال 📢", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"))
        markup.add(types.InlineKeyboardButton("عضو شدم ✅", callback_data="check_join"))
        bot.send_message(user_id, f"سلام ابوالفضل عزیز! برای استفاده از ربات ابتدا باید در کانال عضو شوی 👇", reply_markup=markup)
        return

    send_main_menu(user_id)

def send_main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🛍️ خرید کانفیگ V2Ray", "🎁 دریافت اکانت تست")
    markup.add("📞 پشتیبانی ربات", "👤 حساب کاربری")
    
    if user_id == ADMIN_ID:
        markup.add("⚙️ پنل مدیریت ادمین")
        
    bot.send_message(user_id, "به ربات فروش کانفیگ خوش آمدید! یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=markup)

# ----------------- هینڈلر دکمه‌های پاسخ (Reply) -----------------
@bot.message_handler(commands=['panel'])
def admin_panel_command(message):
    if message.from_user.id == ADMIN_ID:
        send_admin_panel(ADMIN_ID)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    
    if not check_membership(user_id):
        welcome(message)
        return

    if message.text == "🛍️ خرید کانفیگ V2Ray":
        if not sales_status:
            bot.send_message(user_id, "❌ در حال حاضر فروش موقتاً غیرفعال است.")
            return
        
        markup = types.InlineKeyboardMarkup()
        for key, value in PRICES.items():
            markup.add(types.InlineKeyboardButton(value["name"], callback_data=f"buy_{key}"))
        bot.send_message(user_id, "📊 حجم کانفیگ مورد نظر خود را انتخاب کنید:", reply_markup=markup)

    elif message.text == "🎁 دریافت اکانت تست":
        if not test_status:
            bot.send_message(user_id, "❌ دریافت اکانت تست رایگان در حال حاضر غیرفعال است.")
            return
        bot.send_message(user_id, "🔑 اکانت تست شما با موفقیت ساخته شد:\n`vless://test-config-100mb-link...`\n(حجم: 100 مگابایت)")

    elif message.text == "📞 پشتیبانی ربات":
        bot.send_message(user_id, f"🎯 جهت ارتباط با پشتیبانی، ارسال سوالات یا مشکلات فنی به آیدی زیر پیام دهید:\n\n👤 @Abolfazl_Soltani")

    elif message.text == "👤 حساب کاربری":
        account_msg = (f"👤 **مشخصات حساب شما:**\n\n"
                       f"🆔 آیدی عددی: `{user_id}`\n"
                       f"🌍 وضعیت اشتراک کانال: عضو شده ✅")
        bot.send_message(user_id, account_msg, parse_mode="Markdown")

    elif message.text == "⚙️ پنل مدیریت ادمین" and user_id == ADMIN_ID:
        send_admin_panel(user_id)
        
    elif user_id == ADMIN_ID and admin_state.get(user_id) == "waiting_for_broadcast":
        admin_state[user_id] = None
        text_to_send = message.text
        success = 0
        bot.send_message(ADMIN_ID, "⏳ ارسال اعلان همگانی به تمامی اعضا آغاز شد...")
        for u_id in users:
            try:
                bot.send_message(u_id, text_to_send)
                success += 1
                time.sleep(0.05)
            except Exception:
                pass
        bot.send_message(ADMIN_ID, f"📢 اعلان همگانی با موفقیت به پایان رسید.\n✅ تعداد ارسال‌های موفق: {success} از {len(users)}")

    elif user_id == ADMIN_ID and admin_state.get(user_id) == "waiting_for_reject_reason":
        receipt_id = admin_state.get("target_receipt")
        admin_state[user_id] = None
        if receipt_id in pending_receipts:
            buyer_id = pending_receipts[receipt_id]["user_id"]
            bot.send_message(buyer_id, f"❌ فیش ارسالی شما توسط مدیریت رد شد.\n⚠️ **علت رد فیش:** {message.text}\n\nاگر فکر می‌کنید اشتباهی رخ داده، لطفاً با آیدی پشتیبانی (@Abolfazl_Soltani) پیام دهید تا پیگیری شود.")
            bot.send_message(ADMIN_ID, "✅ علت رد فیش ثبت و پیام برای کاربر ارسال شد.")
            del pending_receipts[receipt_id]

# ----------------- پنل مدیریت ادمین -----------------
def send_admin_panel(user_id):
    markup = types.InlineKeyboardMarkup()
    
    t_sales = "🔴 توقف فروش" if sales_status else "🟢 فعالسازی فروش"
    t_test = "🔴 توقف تست" if test_status else "🟢 فعالسازی تست"
    markup.add(types.InlineKeyboardButton(t_sales, callback_data="toggle_sales"),
               types.InlineKeyboardButton(t_test, callback_data="toggle_test"))
    
    markup.add(types.InlineKeyboardButton("📊 آمار درآمد امروز/ماه", callback_data="view_stats"),
               types.InlineKeyboardButton("📢 اعلان همگانی به همه", callback_data="broadcast"))
    
    admin_msg = (f"⚙️ **پنل پیشرفته مدیریت ربات (K2_XAEA)**\n\n"
                 f"👥 کل اعضای ثبت شده: {len(users)}\n"
                 f"🛒 وضعیت سیستم فروش: {'فعال ✅' if sales_status else 'غیرفعال ❌'}\n"
                 f"🎁 وضعیت سیستم اکانت تست: {'فعال ✅' if test_status else 'غیرفعال ❌'}")
    
    bot.send_message(user_id, admin_msg, reply_markup=markup, parse_mode="Markdown")

# ----------------- هینڈلر کالبک‌ها (Inline Buttons) -----------------
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    data = call.data

    if data == "check_join":
        if check_membership(user_id):
            bot.answer_callback_query(call.id, "✅ عضویت شما تایید شد.")
            bot.delete_message(user_id, call.message.message_id)
            send_main_menu(user_id)
        else:
            bot.answer_callback_query(call.id, "❌ شما هنوز در کانال عضو نشده‌اید!", show_alert=True)

    elif data.startswith("buy_"):
        plan_key = data.split("_")[1]
        markup = types.InlineKeyboardMarkup()
        
        p = PRICES[plan_key]
        markup.add(types.InlineKeyboardButton(f"1 ماهه ({p['1month']:,} تومان)", callback_data=f"order_{plan_key}_1month"))
        markup.add(types.InlineKeyboardButton(f"2 ماهه ({p['2month']:,} تومان)", callback_data=f"order_{plan_key}_2month"))
        markup.add(types.InlineKeyboardButton(f"3 ماهه ({p['3month']:,} تومان)", callback_data=f"order_{plan_key}_3month"))
        
        bot.edit_message_text(f"⏱️ دوره زمانی مورد نظر برای کانفیگ **{p['name']}** را انتخاب کنید:", 
                              user_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif data.startswith("order_"):
        _, plan_key, duration = data.split("_")
        price = PRICES[plan_key][duration]
        plan_name = PRICES[plan_key]["name"]
        
        receipt_id = f"REC-{int(time.time())}"
        pending_receipts[receipt_id] = {
            "user_id": user_id,
            "plan": plan_name,
            "duration": duration,
            "price": price
        }
        
        invoice = (f"🧾 **پیش‌فاکتور خرید کانفیگ**\n\n"
                   f"📦 سرویس: {plan_name}\n"
                   f"⏱️ مدت زمان: {duration.replace('month', ' ماهه')}\n"
                   f"💰 مبلغ قابل پرداخت: {price:,} تومان\n\n"
                   f"💳 **اطلاعات کارت جهت واریز:**\n"
                   f"`6037-7012-1103-5784`\n"  # شماره کارت دقیق شما اضافه شد
                   f"👤 **به نام:** ابوالفضل سلطانی\n\n"
                   f"📸 لطفاً پس از واریز وجه، عکس فیش یا اسکرین‌شات پرداخت را مستقیماً در همین جا ارسال کنید.")
        
        bot.edit_message_text(invoice, user_id, call.message.message_id, parse_mode="Markdown")
        bot.register_next_step_handler(call.message, receive_receipt, receipt_id)

    elif user_id == ADMIN_ID:
        if data == "toggle_sales":
            global sales_status
            sales_status = not sales_status
            bot.answer_callback_query(call.id, "وضعیت سیستم فروش تغییر کرد.")
            send_admin_panel(ADMIN_ID)
            
        elif data == "toggle_test":
            global test_status
            test_status = not test_status
            bot.answer_callback_query(call.id, "وضعیت اکانت تست تغییر کرد.")
            send_admin_panel(ADMIN_ID)
            
        elif data == "view_stats":
            stats_msg = (f"📊 **گزارش لحظه‌ای درآمد و فروش ربات**\n\n"
                         f"💰 درآمد امروز شما: {stats['today_income']:,} تومان\n"
                         f"📅 مجموع درآمد این ماه: {stats['month_income']:,} تومان\n"
                         f"🛍️ تعداد کل کانفیگ‌های فروخته شده: {stats['total_sales_count']} عدد")
            bot.send_message(ADMIN_ID, stats_msg, parse_mode="Markdown")
            
        elif data == "broadcast":
            admin_state[ADMIN_ID] = "waiting_for_broadcast"
            bot.send_message(ADMIN_ID, "📝 متن یا اطلاعیه‌ای که می‌خواهید به کل کاربران ربات ارسال شود را بنویسید:")

        elif data.startswith("approve_"):
            rec_id = data.split("_")[1]
            if rec_id in pending_receipts:
                info = pending_receipts[rec_id]
                stats["today_income"] += info["price"]
                stats["month_income"] += info["price"]
                stats["total_sales_count"] += 1
                
                buyer_msg = (f"✅ فیش واریزی شما توسط مدیریت تایید شد!\n\n"
                             f"📦 **مشخصات سفارش شما:**\n"
                             f"نوع کانفیگ: {info['plan']} - {info['duration'].replace('month', ' ماهه')}\n\n"
                             f"🔑 لینک کانفیگ اختصاصی شما صادر شد:\n`vless://your-purchased-config-link-here...`")
                bot.send_message(info["user_id"], buyer_msg, parse_mode="Markdown")
                bot.send_message(ADMIN_ID, "✅ فیش تایید شد و لینک کانفیگ برای خریدار ارسال گردید.")
                del pending_receipts[rec_id]
                
        elif data.startswith("reject_"):
            rec_id = data.split("_")[1]
            admin_state[ADMIN_ID] = "waiting_for_reject_reason"
            admin_state["target_receipt"] = rec_id
            bot.send_message(ADMIN_ID, "❌ علت رد کردن این فیش را بنویسید تا برای کاربر ارسال شود:")

# ----------------- تابع هوشمند دریافت فیش کاربر -----------------
def receive_receipt(message, receipt_id):
    user_id = message.from_user.id
    if message.content_type != 'photo':
        bot.send_message(user_id, "❌ ارسال فیش ناموفق بود. شما باید عکس فیش را ارسال کنید. فرآیند خرید را دوباره شروع کنید.")
        return
    
    if receipt_id not in pending_receipts:
        bot.send_message(user_id, "❌ خطای سیستمی رخ داد. مجدداً اقدام کنید.")
        return

    info = pending_receipts[receipt_id]
    bot.send_message(user_id, "⏳ فیش شما با موفقیت برای مدیریت ارسال شد. پس از بررسی ادمین، لینک کانفیگ همین‌جا برای شما فرستاده می‌شود.")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ تایید فیش و صدور لینک", callback_data=f"approve_{receipt_id}"))
    markup.add(types.InlineKeyboardButton("❌ رد فیش / فیش فیک", callback_data=f"reject_{receipt_id}"))
    
    admin_alert = (f"🚨 **فیش جدید دریافت شد!**\n\n"
                   f"👤 آیدی کاربر خریدار: {user_id}\n"
                   f"📦 سرویس: {info['plan']} ({info['duration'].replace('month', ' ماهه')})\n"
                   f"💰 مبلغ واریزی: {info['price']:,} تومان\n"
                   f"🆔 شناسه تراکنش: `{receipt_id}`")
    
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=admin_alert, reply_markup=markup, parse_mode="Markdown")

# ----------------- اجرای مداوم ربات در Termux -----------------
bot.infinity_polling()
