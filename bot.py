import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ========== НАСТРОЙКИ ==========
TOKEN = "8693007147:AAHqyn8Aekty-r8TJB86miVPDVe9cObYejM"
ADMIN_ID = 1595538164
COMMISSION = 15  # 15% гаранту
PAYMENT_DETAILS = "💳 2200 1536 8048 9946\n🏦 Альфа-Банк"
BOT_USERNAME = "morskoooy_booy_bot"
REVIEW_TAG = "@noflixx"
# ================================

# Отключаем логи
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)

# Файлы для хранения данных
DEALS_FILE = "deals.json"
CHATS_FILE = "chats.json"
USER_DATA_FILE = "user_data.json"
USERS_FILE = "users.json"
REVIEWS_FILE = "reviews.json"
MESSAGES_FILE = "messages.json"

# ========== РАБОТА С JSON ==========
def load_data(filename):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
# ====================================

# ========== РАБОТА С USER_DATA ==========
def load_user_data():
    return load_data(USER_DATA_FILE)

def save_user_data(data):
    save_data(USER_DATA_FILE, data)

def get_user_step(user_id):
    data = load_user_data()
    return data.get(str(user_id), {}).get('step')

def set_user_step(user_id, step, **kwargs):
    data = load_user_data()
    if str(user_id) not in data:
        data[str(user_id)] = {}
    data[str(user_id)]['step'] = step
    for key, value in kwargs.items():
        data[str(user_id)][key] = value
    save_user_data(data)

def clear_user_step(user_id):
    data = load_user_data()
    if str(user_id) in data:
        del data[str(user_id)]
        save_user_data(data)
# =========================================

# ========== РАБОТА С ПОЛЬЗОВАТЕЛЯМИ ==========
def load_users():
    return load_data(USERS_FILE)

def save_user_info(user_id, username, full_name):
    users = load_users()
    users[str(user_id)] = {
        'user_id': user_id,
        'username': username,
        'full_name': full_name
    }
    save_data(USERS_FILE, users)

def user_exists(username):
    users = load_users()
    username_clean = username.replace('@', '').lower()
    for user_data in users.values():
        if user_data.get('username') and user_data['username'].lower() == username_clean:
            return user_data['user_id']
    return None
# =============================================

# ========== РАБОТА С ОТЗЫВАМИ ==========
def load_reviews():
    return load_data(REVIEWS_FILE)

def save_review(deal_id, from_user, to_user, text):
    """Сохранить отзыв"""
    reviews = load_reviews()
    if deal_id not in reviews:
        reviews[deal_id] = []
    
    reviews[deal_id].append({
        'from': from_user,
        'to': to_user,
        'text': text,
        'date': str(update.effective_message.date)
    })
    save_data(REVIEWS_FILE, reviews)

def get_deal_reviews(deal_id):
    """Получить отзывы по сделке"""
    reviews = load_reviews()
    return reviews.get(deal_id, [])
# =========================================

# ========== ЛИЧНЫЕ СООБЩЕНИЯ АДМИНУ ==========
def load_messages():
    return load_data(MESSAGES_FILE)

def save_message(user_id, username, message_text):
    """Сохранить сообщение админу"""
    messages = load_messages()
    if str(user_id) not in messages:
        messages[str(user_id)] = []
    
    messages[str(user_id)].append({
        'text': message_text,
        'date': str(update.effective_message.date),
        'username': username
    })
    save_data(MESSAGES_FILE, messages)

def get_user_messages(user_id):
    """Получить сообщения пользователя"""
    messages = load_messages()
    return messages.get(str(user_id), [])
# =============================================

# ========== КОМАНДЫ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт - показывает меню и сохраняет пользователя"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name
    save_user_info(user_id, username, full_name)
    
    await show_main_menu(update, context)

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /menu - открыть меню"""
    await show_main_menu(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help - помощь"""
    text = (
        "❓ **Помощь по боту**\n\n"
        "🔹 **Как создать сделку?**\n"
        "• Нажми «Создать сделку» в меню\n\n"
        "🔹 **Как присоединиться к сделке?**\n"
        "Если вас пригласили, нажмите кнопку «Присоединиться»\n\n"
        "🔹 **Как проходит сделка?**\n"
        "1. Оба подтверждают участие (каждый получает свою кнопку)\n"
        "2. Админ может подтвердить за двоих одной кнопкой\n"
        "3. Покупатель оплачивает и отправляет скриншот\n"
        "4. Продавец передаёт товар и указывает карту\n"
        "5. Админ подтверждает завершение\n"
        "6. Можно оставить отзыв\n\n"
        f"🔹 **Комиссия гаранта:** {COMMISSION}%\n"
        f"🔹 **Тег для отзывов:** {REVIEW_TAG}\n\n"
        "📋 **Команды:**\n"
        "/start - Главное меню\n"
        "/menu - Открыть меню\n"
        "/help - Эта помощь\n"
        "/mydeals - Мои сделки\n"
        "/reviews - Мои отзывы\n"
        "/messages - Сообщения админу\n"
        "/cancel - Отменить действие"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]]
    
    if update.message:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помощь из меню"""
    query = update.callback_query
    await query.answer()
    await help_command(update, context)

async def mydeals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /mydeals - мои сделки"""
    await show_my_deals(update, context)

async def reviews_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /reviews - мои отзывы"""
    await show_my_reviews(update, context)

async def messages_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /messages - мои сообщения админу"""
    await show_my_messages(update, context)

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /cancel - отменить действие"""
    user_id = update.effective_user.id
    clear_user_step(user_id)
    
    await update.message.reply_text(
        "✅ Действие отменено.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 В меню", callback_data="back_to_menu")
        ]])
    )

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать главное меню"""
    keyboard = [
        [InlineKeyboardButton("🤝 Создать сделку", callback_data="new_deal")],
        [InlineKeyboardButton("📋 Мои сделки", callback_data="my_deals")],
        [InlineKeyboardButton("📝 Мои отзывы", callback_data="my_reviews")],
        [InlineKeyboardButton("💬 Написать админу", callback_data="write_to_admin")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    
    if update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("👑 Админ панель", callback_data="admin_panel")])
    
    if update.message:
        await update.message.reply_text(
            "🔹 **Главное меню** 🔹",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            "🔹 **Главное меню** 🔹",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в главное меню"""
    query = update.callback_query
    await query.answer()
    await show_main_menu(update, context)

# ========== ПРОСМОТР СВОИХ СДЕЛОК ==========
async def show_my_deals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр своих сделок"""
    user_id = update.effective_user.id
    deals = load_data(DEALS_FILE)
    chats = load_data(CHATS_FILE)
    
    user_deals = []
    if str(user_id) in chats:
        for deal_id in chats[str(user_id)]:
            if deal_id in deals:
                deal = deals[deal_id]
                status_text = {
                    'waiting_for_second_user': '⏳ Ожидание второго',
                    'waiting_confirmation': '⏳ Ждём подтверждения',
                    'waiting_for_payment': '💰 Ожидание оплаты',
                    'waiting_screenshot': '📸 Ждём скриншот',
                    'waiting_for_card': '💳 Ждём карту',
                    'waiting_admin_confirm': '👑 Ждём админа',
                    'completed': '✅ Завершена'
                }.get(deal['status'], deal['status'])
                
                user_role = "продавец" if user_id == deal.get('seller_id') else "покупатель"
                
                deal_text = f"🔹 **Сделка #{deal_id}**\nРоль: {user_role}\nСтатус: {status_text}\nПредмет: {deal['product']}\n"
                
                if user_role == "продавец" and deal.get('card_number'):
                    deal_text += f"💳 Ваша карта: {deal['card_number']} ({deal.get('bank_name', '?')})\n"
                
                user_deals.append(deal_text)
    
    text = "📋 **Ваши сделки:**\n\n" + "\n".join(user_deals) if user_deals else "📭 Нет активных сделок."
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
    
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# ========== ПРОСМОТР ОТЗЫВОВ ==========
async def show_my_reviews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр своих отзывов"""
    user_id = update.effective_user.id
    username = f"@{update.effective_user.username}"
    reviews = load_reviews()
    
    my_reviews = []
    for deal_id, deal_reviews in reviews.items():
        for review in deal_reviews:
            if review['to'] == username:
                my_reviews.append(f"🔹 **Сделка #{deal_id}**\nОт: {review['from']}\nОтзыв: {review['text']}\n")
    
    text = "📝 **Ваши отзывы:**\n\n" + "\n".join(my_reviews) if my_reviews else "📭 У вас пока нет отзывов."
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
    
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# ========== НАПИСАТЬ АДМИНУ ==========
async def write_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Написать сообщение админу"""
    query = update.callback_query
    await query.answer()
    
    set_user_step(query.from_user.id, 'writing_to_admin')
    
    await query.edit_message_text(
        f"✍️ Напишите сообщение для администратора. {REVIEW_TAG}\n/cancel - отмена"
    )

async def handle_message_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщения админу"""
    user_id = update.effective_user.id
    if get_user_step(user_id) != 'writing_to_admin':
        return
    
    message_text = update.message.text
    username = f"@{update.effective_user.username}"
    
    save_message(user_id, username, message_text)
    clear_user_step(user_id)
    
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📨 **Сообщение от {username}**\n\n{message_text}\n\n{REVIEW_TAG}",
        parse_mode="Markdown"
    )
    
    await update.message.reply_text("✅ Сообщение отправлено!", reply_markup=InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 В меню", callback_data="back_to_menu")
    ]]))

async def show_my_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр своих сообщений админу"""
    user_id = update.effective_user.id
    messages = get_user_messages(user_id)
    
    if not messages:
        text = "📭 У вас пока нет сообщений админу."
    else:
        text = "💬 **Ваши сообщения:**\n\n"
        for msg in messages[-5:]:
            text += f"• {msg['text']}\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
    
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# ========== СОЗДАНИЕ СДЕЛКИ ==========
async def new_deal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало создания сделки"""
    query = update.callback_query
    await query.answer()
    
    set_user_step(query.from_user.id, 'waiting_for_username')
    await query.edit_message_text("📝 Введите @username второго участника:")

async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение username"""
    user_id = update.effective_user.id
    if get_user_step(user_id) != 'waiting_for_username':
        return
    
    username = update.message.text.strip()
    if not username.startswith('@'):
        username = '@' + username
    
    second_user_id = user_exists(username)
    
    set_user_step(user_id, 'waiting_for_role', second_username=username, second_user_id=second_user_id)
    
    keyboard = [
        [InlineKeyboardButton("💰 Я продавец", callback_data="role_seller")],
        [InlineKeyboardButton("🛒 Я покупатель", callback_data="role_buyer")]
    ]
    
    await update.message.reply_text("Выберите вашу роль:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор роли"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = load_user_data().get(str(user_id), {})
    
    if user_data.get('step') != 'waiting_for_role':
        return
    
    role = "seller" if query.data == "role_seller" else "buyer"
    
    set_user_step(user_id, 'waiting_for_product', 
                  second_username=user_data['second_username'],
                  second_user_id=user_data['second_user_id'],
                  role=role)
    
    await query.edit_message_text("📦 Напишите, что передаётся:")

async def handle_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение товара и отправка приглашения второму участнику"""
    user_id = update.effective_user.id
    user_data = load_user_data().get(str(user_id), {})
    
    if user_data.get('step') != 'waiting_for_product':
        return
    
    product = update.message.text
    second_username = user_data['second_username']
    second_user_id = user_data['second_user_id']
    creator_role = user_data['role']
    
    deals = load_data(DEALS_FILE)
    deal_id = str(len(deals) + 1)
    
    # Определяем роли
    if creator_role == "seller":
        seller_id = user_id
        seller_username = update.effective_user.username
        seller_name = update.effective_user.full_name
        buyer_id = None
        buyer_username = None
        buyer_name = None
    else:
        seller_id = None
        seller_username = None
        seller_name = None
        buyer_id = user_id
        buyer_username = update.effective_user.username
        buyer_name = update.effective_user.full_name
    
    deals[deal_id] = {
        'product': product,
        'seller_id': seller_id,
        'seller_username': seller_username,
        'seller_name': seller_name,
        'buyer_id': buyer_id,
        'buyer_username': buyer_username,
        'buyer_name': buyer_name,
        'second_username': second_username,
        'second_user_id': second_user_id,
        'seller_confirm': False,
        'buyer_confirm': False,
        'buyer_paid': False,
        'seller_ready': False,
        'status': 'waiting_for_second_user',
        'created_by': user_id,
        'card_number': None,
        'bank_name': None,
        'screenshot': None
    }
    save_data(DEALS_FILE, deals)
    
    chats = load_data(CHATS_FILE)
    if str(user_id) not in chats:
        chats[str(user_id)] = []
    chats[str(user_id)].append(deal_id)
    save_data(CHATS_FILE, chats)
    
    clear_user_step(user_id)
    
    await update.message.reply_text(f"✅ Сделка #{deal_id} создана!")
    
    # 👇 ОТПРАВКА УВЕДОМЛЕНИЯ ВТОРОМУ УЧАСТНИКУ
    if second_user_id:
        try:
            role_for_second = "покупатель" if creator_role == "seller" else "продавец"
            
            await context.bot.send_message(
                chat_id=second_user_id,
                text=f"🔔 **Вас пригласили в сделку #{deal_id}!**\n\n"
                     f"👤 Пригласил: {update.effective_user.full_name} (@{update.effective_user.username})\n"
                     f"📦 Предмет: {product}\n"
                     f"💰 Комиссия гаранта: {COMMISSION}%\n\n"
                     f"Ваша роль: **{role_for_second}**\n\n"
                     f"Чтобы присоединиться, нажмите кнопку ниже:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ Присоединиться к сделке", callback_data=f"join_{deal_id}")
                ]]),
                parse_mode="Markdown"
            )
            logger.info(f"Уведомление отправлено {second_user_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
            await update.message.reply_text(
                f"⚠️ Не удалось отправить уведомление {second_username}\n"
                f"Пользователь должен написать боту: @{BOT_USERNAME}"
            )
    else:
        await update.message.reply_text(
            f"⚠️ Пользователь {second_username} ещё не писал боту.\n"
            f"Ему нужно написать: @{BOT_USERNAME}"
        )

# ========== ПРИСОЕДИНЕНИЕ К СДЕЛКЕ ==========
async def join_deal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Присоединение к сделке - С КНОПКОЙ ПОДТВЕРЖДЕНИЯ!"""
    query = update.callback_query
    await query.answer()
    
    deal_id = query.data.replace('join_', '')
    deals = load_data(DEALS_FILE)
    deal = deals.get(deal_id)
    
    if not deal or deal['status'] != 'waiting_for_second_user':
        await query.edit_message_text("❌ Сделка не найдена")
        return
    
    username = f"@{query.from_user.username}"
    if username.lower() != deal['second_username'].lower():
        await query.edit_message_text("❌ Это не ваша сделка")
        return
    
    # Определяем роль второго участника
    if deal['seller_id'] is None:
        deal['seller_id'] = query.from_user.id
        deal['seller_username'] = query.from_user.username
        deal['seller_name'] = query.from_user.full_name
        role = "seller"
        role_text = "продавец"
    else:
        deal['buyer_id'] = query.from_user.id
        deal['buyer_username'] = query.from_user.username
        deal['buyer_name'] = query.from_user.full_name
        role = "buyer"
        role_text = "покупатель"
    
    deal['status'] = 'waiting_confirmation'
    save_data(DEALS_FILE, deals)
    
    # Сохраняем в чаты
    chats = load_data(CHATS_FILE)
    if str(query.from_user.id) not in chats:
        chats[str(query.from_user.id)] = []
    chats[str(query.from_user.id)].append(deal_id)
    save_data(CHATS_FILE, chats)
    
    # 👇 КНОПКА ДЛЯ ПРИСОЕДИНИВШЕГОСЯ УЧАСТНИКА
    keyboard = [[InlineKeyboardButton(f"✅ Подтвердить участие как {role_text}", callback_data=f"confirm_{role}_{deal_id}")]]
    
    await query.edit_message_text(
        f"✅ Вы присоединились к сделке #{deal_id}!\n\n"
        f"📦 Предмет: {deal['product']}\n"
        f"👤 Продавец: @{deal['seller_username']}\n"
        f"👤 Покупатель: @{deal['buyer_username']}\n"
        f"💰 Комиссия: {COMMISSION}%\n\n"
        f"**Ваша роль:** {role_text}\n\n"
        f"Нажмите кнопку ниже для подтверждения участия:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    # 👇 КНОПКА ДЛЯ ПЕРВОГО УЧАСТНИКА (СОЗДАТЕЛЯ)
    # Определяем роль первого участника
    first_user_id = deal['created_by']
    if first_user_id == deal.get('seller_id'):
        first_role = "seller"
        first_role_text = "продавец"
    else:
        first_role = "buyer"
        first_role_text = "покупатель"
    
    first_keyboard = [[InlineKeyboardButton(f"✅ Подтвердить участие как {first_role_text}", callback_data=f"confirm_{first_role}_{deal_id}")]]
    
    await context.bot.send_message(
        chat_id=first_user_id,
        text=f"👤 **{role_text.capitalize()}** присоединился к сделке #{deal_id}!\n\n"
             f"📦 Предмет: {deal['product']}\n"
             f"👤 Продавец: @{deal['seller_username']}\n"
             f"👤 Покупатель: @{deal['buyer_username']}\n"
             f"💰 Комиссия: {COMMISSION}%\n\n"
             f"**Ваша роль:** {first_role_text}\n\n"
             f"Теперь вам нужно подтвердить участие:",
        reply_markup=InlineKeyboardMarkup(first_keyboard),
        parse_mode="Markdown"
    )
    
    # Уведомление админу
    await send_admin_update(context, deal_id, deal)

# ========== ПОДТВЕРЖДЕНИЕ УЧАСТИЯ ==========
async def send_admin_update(context, deal_id, deal):
    """Отправить обновление админу"""
    text = (
        f"🔄 **Сделка #{deal_id}**\n\n"
        f"📦 Предмет: {deal['product']}\n"
        f"👤 Продавец: @{deal['seller_username']}\n"
        f"👤 Покупатель: @{deal['buyer_username']}\n\n"
        f"**Статус подтверждения:**\n"
        f"Продавец: {'✅' if deal.get('seller_confirm') else '❌'}\n"
        f"Покупатель: {'✅' if deal.get('buyer_confirm') else '❌'}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="Markdown")

async def handle_confirm_seller(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение продавца"""
    query = update.callback_query
    await query.answer()
    
    deal_id = query.data.replace('confirm_seller_', '')
    deals = load_data(DEALS_FILE)
    deal = deals.get(deal_id)
    
    if not deal:
        await query.edit_message_text("❌ Сделка не найдена")
        return
    
    # Проверяем, что это продавец или админ
    if query.from_user.id == deal['seller_id'] or query.from_user.id == ADMIN_ID:
        deal['seller_confirm'] = True
        save_data(DEALS_FILE, deals)
        
        await query.edit_message_text("✅ Вы подтвердили участие как продавец!")
        await send_admin_update(context, deal_id, deal)
        
        # Проверяем, подтвердили ли оба
        if deal.get('seller_confirm') and deal.get('buyer_confirm'):
            deal['status'] = 'waiting_for_payment'
            save_data(DEALS_FILE, deals)
            
            # Покупателю - кнопка оплаты
            await context.bot.send_message(
                chat_id=deal['buyer_id'],
                text=f"✅ **Оба подтвердили сделку #{deal_id}!**\n\n"
                     f"📦 Предмет: {deal['product']}\n"
                     f"💰 Комиссия: {COMMISSION}%\n\n"
                     f"Теперь оплатите:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("💳 Оплатить", callback_data=f"pay_{deal_id}")
                ]]),
                parse_mode="Markdown"
            )
            
            # Продавцу - уведомление
            await context.bot.send_message(
                chat_id=deal['seller_id'],
                text=f"✅ **Оба подтвердили сделку #{deal_id}!**\n\n"
                     f"Ожидание оплаты от покупателя..."
            )
    else:
        await query.edit_message_text("❌ Вы не продавец в этой сделке")

async def handle_confirm_buyer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение покупателя"""
    query = update.callback_query
    await query.answer()
    
    deal_id = query.data.replace('confirm_buyer_', '')
    deals = load_data(DEALS_FILE)
    deal = deals.get(deal_id)
    
    if not deal:
        await query.edit_message_text("❌ Сделка не найдена")
        return
    
    # Проверяем, что это покупатель или админ
    if query.from_user.id == deal['buyer_id'] or query.from_user.id == ADMIN_ID:
        deal['buyer_confirm'] = True
        save_data(DEALS_FILE, deals)
        
        await query.edit_message_text("✅ Вы подтвердили участие как покупатель!")
        await send_admin_update(context, deal_id, deal)
        
        # Проверяем, подтвердили ли оба
        if deal.get('seller_confirm') and deal.get('buyer_confirm'):
            deal['status'] = 'waiting_for_payment'
            save_data(DEALS_FILE, deals)
            
            # Покупателю - кнопка оплаты
            await context.bot.send_message(
                chat_id=deal['buyer_id'],
                text=f"✅ **Оба подтвердили сделку #{deal_id}!**\n\n"
                     f"📦 Предмет: {deal['product']}\n"
                     f"💰 Комиссия: {COMMISSION}%\n\n"
                     f"Теперь оплатите:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("💳 Оплатить", callback_data=f"pay_{deal_id}")
]]),
                parse_mode="Markdown"
            )
            
            # Продавцу - уведомление
            await context.bot.send_message(
                chat_id=deal['seller_id'],
                text=f"✅ **Оба подтвердили сделку #{deal_id}!**\n\n"
                     f"Ожидание оплаты от покупателя..."
            )
    else:
        await query.edit_message_text("❌ Вы не покупатель в этой сделке")

# ========== ОПЛАТА ==========
async def handle_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Оплата"""
    query = update.callback_query
    await query.answer()
    
    deal_id = query.data.replace('pay_', '')
    deals = load_data(DEALS_FILE)
    deal = deals.get(deal_id)
    
    if not deal:
        await query.edit_message_text("❌ Сделка не найдена")
        return
    
    deal['status'] = 'waiting_screenshot'
    save_data(DEALS_FILE, deals)
    
    await query.edit_message_text(
        f"💳 **Реквизиты для оплаты:**\n\n"
        f"{PAYMENT_DETAILS}\n\n"
        f"📦 Сделка #{deal_id}\n"
        f"💰 Сумма: уточните у продавца\n\n"
        f"После оплаты **отправьте скриншот** (фото):",
        parse_mode="Markdown"
    )

async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение скриншота"""
    if not update.message.photo:
        return
    
    user_id = update.effective_user.id
    deals = load_data(DEALS_FILE)
    
    for deal_id, deal in deals.items():
        if deal.get('buyer_id') == user_id and deal['status'] == 'waiting_screenshot':
            photo = update.message.photo[-1]
            deal['screenshot'] = photo.file_id
            deal['status'] = 'screenshot_received'
            deal['buyer_paid'] = True
            save_data(DEALS_FILE, deals)
            
            await update.message.reply_text("✅ Скриншот получен!")
            
            # Отправляем скриншот продавцу с кнопкой
            await context.bot.send_photo(
                chat_id=deal['seller_id'],
                photo=photo.file_id,
                caption=f"🖼️ Скриншот оплаты по сделке #{deal_id}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📦 Я передал товар", callback_data=f"ready_{deal_id}")
                ]])
            )
            return

# ========== ПРОДАВЕЦ ПЕРЕДАЛ ТОВАР ==========
async def handle_ready(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Продавец передал товар"""
    query = update.callback_query
    await query.answer()
    
    deal_id = query.data.replace('ready_', '')
    deals = load_data(DEALS_FILE)
    deal = deals.get(deal_id)
    
    if not deal:
        await query.edit_message_text("❌ Сделка не найдена")
        return
    
    keyboard = [[InlineKeyboardButton("✅ Подтвердить передачу", callback_data=f"ready_confirm_{deal_id}")]]
    await query.edit_message_text(
        "📦 Подтвердите передачу товара:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_ready_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение передачи товара"""
    query = update.callback_query
    await query.answer()
    
    deal_id = query.data.replace('ready_confirm_', '')
    deals = load_data(DEALS_FILE)
    deal = deals.get(deal_id)
    
    if not deal:
        await query.edit_message_text("❌ Сделка не найдена")
        return
    
    deal['seller_ready'] = True
    deal['status'] = 'waiting_for_card'
    save_data(DEALS_FILE, deals)
    
    set_user_step(query.from_user.id, 'waiting_for_card', deal_id=deal_id)
    await query.edit_message_text("💳 Введите номер карты для получения денег:")

async def handle_card_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение карты"""
    user_id = update.effective_user.id
    user_data = load_user_data().get(str(user_id), {})
    
    if user_data.get('step') != 'waiting_for_card':
        return
    
    card = update.message.text
    deal_id = user_data['deal_id']
    deals = load_data(DEALS_FILE)
    deal = deals.get(deal_id)
    
    if not deal:
        return
    
    deal['card_number'] = card
    save_data(DEALS_FILE, deals)
    
    set_user_step(user_id, 'waiting_for_bank', deal_id=deal_id)
    await update.message.reply_text("🏦 Введите название банка:")

async def handle_bank_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение банка"""
    user_id = update.effective_user.id
    user_data = load_user_data().get(str(user_id), {})
    
    if user_data.get('step') != 'waiting_for_bank':
        return
    
    bank = update.message.text
    deal_id = user_data['deal_id']
    deals = load_data(DEALS_FILE)
    deal = deals.get(deal_id)
    
    if not deal:
        return
    
    deal['bank_name'] = bank
    deal['status'] = 'waiting_admin_confirm'
    save_data(DEALS_FILE, deals)
    clear_user_step(user_id)
    
    await update.message.reply_text("✅ Данные сохранены! Ожидайте подтверждения админа.")
    
    # Уведомление покупателю
    await context.bot.send_message(
        chat_id=deal['buyer_id'],
        text=f"📦 Продавец подтвердил передачу товара по сделке #{deal_id}!\n\n"
             f"💳 Карта продавца: {card} ({bank})\n\n"
             f"⏳ Ожидайте подтверждения администратора."
    )
    
    # Уведомление админу с кнопкой
    admin_keyboard = [[InlineKeyboardButton("✅ Завершить сделку", callback_data=f"approve_{deal_id}")]]
    
    if deal.get('screenshot'):
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=deal['screenshot'],
            caption=f"✅ **Сделка #{deal_id} готова!**\n\n"
                    f"📦 Предмет: {deal['product']}\n"
                    f"👤 Продавец: @{deal['seller_username']}\n"
                    f"💳 Карта: {card} ({bank})\n"
                    f"👤 Покупатель: @{deal['buyer_username']}\n"
                    f"💰 Комиссия: {COMMISSION}%\n\n"
                    f"🖼️ Скриншот оплаты (выше)\n"
                    f"📦 Товар передан ✅",
            reply_markup=InlineKeyboardMarkup(admin_keyboard),
            parse_mode="Markdown"
        )
    else:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"✅ **Сделка #{deal_id} готова!**\n\n"
                 f"📦 Предмет: {deal['product']}\n"
                 f"👤 Продавец: @{deal['seller_username']}\n"
                 f"💳 Карта: {card} ({bank})\n"
                 f"👤 Покупатель: @{deal['buyer_username']}\n"
                 f"💰 Комиссия: {COMMISSION}%\n\n"
                 f"Покупатель оплатил ✅\n"
                 f"Товар передан ✅",
            reply_markup=InlineKeyboardMarkup(admin_keyboard),
            parse_mode="Markdown"
        )

# ========== ПОДТВЕРЖДЕНИЕ АДМИНА ==========
async def handle_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ завершает сделку"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("⛔ Нет прав")
        return
    
    deal_id = query.data.replace('approve_', '')
    deals = load_data(DEALS_FILE)
    deal = deals.get(deal_id)
    
    if not deal:
        await query.edit_message_text("❌ Сделка не найдена")
        return
    
    deal['status'] = 'completed'
    save_data(DEALS_FILE, deals)
    
    # Уведомление обоим
    for user_id in [deal['seller_id'], deal['buyer_id']]:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ **Сделка #{deal_id} завершена!**\n\n"
                 f"📦 Предмет: {deal['product']}\n"
                 f"💰 Комиссия {COMMISSION}% удержана.\n\n"
                 f"Спасибо! {REVIEW_TAG}"
        )
    
    await query.edit_message_text(f"✅ Сделка #{deal_id} завершена!")

# ========== АДМИН ПАНЕЛЬ ==========
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ панель"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        return
    
    deals = load_data(DEALS_FILE)
    
    total = len(deals)
    waiting = sum(1 for d in deals.values() if d['status'] == 'waiting_confirmation')
    payment = sum(1 for d in deals.values() if d['status'] == 'waiting_for_payment')
    confirm = sum(1 for d in deals.values() if d['status'] == 'waiting_admin_confirm')
    
    keyboard = [
        [InlineKeyboardButton(f"⏳ Ожидают подтверждения ({waiting})", callback_data="admin_waiting")],
        [InlineKeyboardButton(f"👑 Готовы к завершению ({confirm})", callback_data="admin_ready")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
    ]
    
    text = (
        f"👑 **Админ панель**\n\n"
        f"📊 Всего сделок: {total}\n"
        f"⏳ Ожидают: {waiting}\n"
        f"💰 Оплачивают: {payment}\n"
        f"✅ Готовы: {confirm}"
    )
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def admin_waiting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сделки, ожидающие подтверждения участников"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        return
    
    deals = load_data(DEALS_FILE)
    waiting = []
    
    for deal_id, deal in deals.items():
        if deal['status'] == 'waiting_confirmation':
            waiting.append((deal_id, deal))
    
    if not waiting:
        await query.edit_message_text(
            "✅ Нет ожидающих",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")
            ]])
        )
        return
    
    text = "⏳ **Сделки, ожидающие подтверждения:**\n\n"
    keyboard = []
    
    for deal_id, deal in waiting:
        status = (f"Продавец: {'✅' if deal.get('seller_confirm') else '❌'} | "
                  f"Покупатель: {'✅' if deal.get('buyer_confirm') else '❌'}")
        text += f"🔹 #{deal_id}: {deal['product']}\n   {status}\n\n"
        
        # Кнопка для админа (подтвердить за двоих)
        keyboard.append([InlineKeyboardButton(f"✅ Подтвердить #{deal_id} (за двоих)", callback_data=f"admin_confirm_both_{deal_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def admin_ready(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сделки, готовые к завершению"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        return
    
    deals = load_data(DEALS_FILE)
    ready = []
    
    for deal_id, deal in deals.items():
        if deal['status'] == 'waiting_admin_confirm':
            ready.append((deal_id, deal))
    
    if not ready:
        await query.edit_message_text(
            "✅ Нет готовых сделок",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")
            ]])
        )
        return
    
    text = "👑 **Сделки, готовые к завершению:**\n\n"
    keyboard = []
    
    for deal_id, deal in ready:
        text += f"🔹 #{deal_id}: {deal['product']}\n"
        text += f"   💳 Карта: {deal.get('card_number', '?')} ({deal.get('bank_name', '?')})\n\n"
        keyboard.append([InlineKeyboardButton(f"✅ Завершить #{deal_id}", callback_data=f"approve_{deal_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        return
    
    deals = load_data(DEALS_FILE)
    
    total = len(deals)
    completed = sum(1 for d in deals.values() if d['status'] == 'completed')
    waiting_second = sum(1 for d in deals.values() if d['status'] == 'waiting_for_second_user')
    waiting_confirm = sum(1 for d in deals.values() if d['status'] == 'waiting_confirmation')
    waiting_payment = sum(1 for d in deals.values() if d['status'] == 'waiting_for_payment')
    waiting_screenshot = sum(1 for d in deals.values() if d['status'] == 'waiting_screenshot')
    waiting_card = sum(1 for d in deals.values() if d['status'] == 'waiting_for_card')
    waiting_admin = sum(1 for d in deals.values() if d['status'] == 'waiting_admin_confirm')
    
    text = (
        f"📊 **Статистика**\n\n"
        f"📌 Всего: {total}\n"
        f"✅ Завершено: {completed}\n"
        f"⏳ Ожидание 2-го: {waiting_second}\n"
        f"⏳ Подтверждение: {waiting_confirm}\n"
        f"💰 Оплата: {waiting_payment}\n"
        f"📸 Скриншот: {waiting_screenshot}\n"
        f"💳 Карта: {waiting_card}\n"
        f"👑 Готово: {waiting_admin}"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def admin_confirm_both(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ подтверждает за двоих"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        return
    
    deal_id = query.data.replace('admin_confirm_both_', '')
    deals = load_data(DEALS_FILE)
    deal = deals.get(deal_id)
    
    if not deal:
        await query.edit_message_text("❌ Сделка не найдена")
        return
    
    # Подтверждаем за обоих
    deal['seller_confirm'] = True
    deal['buyer_confirm'] = True
    deal['status'] = 'waiting_for_payment'
    save_data(DEALS_FILE, deals)
    
    # Уведомление продавцу
    await context.bot.send_message(
        chat_id=deal['seller_id'],
        text=f"👑 **Администратор подтвердил ваше участие в сделке #{deal_id}!**\n\n"
             f"Ожидайте оплаты от покупателя."
    )
    
    # Уведомление покупателю с кнопкой оплаты
    await context.bot.send_message(
        chat_id=deal['buyer_id'],
        text=f"👑 **Администратор подтвердил сделку #{deal_id}!**\n\n"
             f"📦 Предмет: {deal['product']}\n"
             f"💰 Комиссия: {COMMISSION}%\n\n"
             f"Теперь оплатите:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("💳 Оплатить", callback_data=f"pay_{deal_id}")
        ]]),
        parse_mode="Markdown"
    )
    
    await query.edit_message_text(f"✅ Сделка #{deal_id} подтверждена за обоих!")

# ========== ОБЩИЙ ОБРАБОТЧИК ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Общий обработчик"""
    user_id = update.effective_user.id
    step = get_user_step(user_id)
    
    if step == 'writing_to_admin':
        await handle_message_to_admin(update, context)
    elif step == 'waiting_for_username':
        await handle_username(update, context)
    elif step == 'waiting_for_product':
        await handle_product(update, context)
    elif step == 'waiting_for_card':
        await handle_card_number(update, context)
    elif step == 'waiting_for_bank':
        await handle_bank_name(update, context)
    elif update.message.photo:
        await handle_screenshot(update, context)

# ========== ЗАПУСК ==========
def main():
    print("🚀 Запуск гарант-бота...")
    print("✅ Бот работает! (логи отключены)")
    
    app = Application.builder().token(TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("mydeals", mydeals_command))
    app.add_handler(CommandHandler("reviews", reviews_command))
    app.add_handler(CommandHandler("messages", messages_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    
    # Меню
    app.add_handler(CallbackQueryHandler(new_deal, pattern="^new_deal$"))
    app.add_handler(CallbackQueryHandler(show_my_deals, pattern="^my_deals$"))
    app.add_handler(CallbackQueryHandler(show_my_reviews, pattern="^my_reviews$"))
    app.add_handler(CallbackQueryHandler(write_to_admin, pattern="^write_to_admin$"))
    app.add_handler(CallbackQueryHandler(help_menu, pattern="^help$"))
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern="^back_to_menu$"))
    
    # Админка
    app.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin_panel$"))
    app.add_handler(CallbackQueryHandler(admin_waiting, pattern="^admin_waiting$"))
    app.add_handler(CallbackQueryHandler(admin_ready, pattern="^admin_ready$"))
    app.add_handler(CallbackQueryHandler(admin_stats, pattern="^admin_stats$"))
    app.add_handler(CallbackQueryHandler(admin_confirm_both, pattern="^admin_confirm_both_"))
    
    # Сделки
    app.add_handler(CallbackQueryHandler(join_deal, pattern="^join_"))
    app.add_handler(CallbackQueryHandler(handle_role, pattern="^role_"))
    app.add_handler(CallbackQueryHandler(handle_confirm_seller, pattern="^confirm_seller_"))
    app.add_handler(CallbackQueryHandler(handle_confirm_buyer, pattern="^confirm_buyer_"))
    app.add_handler(CallbackQueryHandler(handle_pay, pattern="^pay_"))
    app.add_handler(CallbackQueryHandler(handle_ready, pattern="^ready_"))
    app.add_handler(CallbackQueryHandler(handle_ready_confirm, pattern="^ready_confirm_"))
    app.add_handler(CallbackQueryHandler(handle_approve, pattern="^approve_"))
    
    # Сообщения
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_message))
    
    print("✅ Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
