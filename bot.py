import os
import json
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEB_APP_URL = os.environ.get('WEB_APP_URL')
ADMIN_ID = 198218873

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет ReplyKeyboard с кнопкой WebApp"""
    user = update.effective_user
    logger.info(f"🟢 Пользователь {user.id} (@{user.username}) запустил бота")
    
    # ВАЖНО: Используем ReplyKeyboard, НЕ InlineKeyboard!
    keyboard = [[KeyboardButton("📝 Заполнить бриф", web_app=WebAppInfo(url=WEB_APP_URL))]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я бот для сбора брифов.\n"
        "Нажми кнопку ниже, чтобы заполнить бриф.",
        reply_markup=reply_markup
    )

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает данные из Web App"""
    try:
        user = update.effective_user
        logger.info(f"🔥 ПОЛУЧЕНЫ ДАННЫЕ от {user.id}")
        
        raw_data = update.effective_message.web_app_data.data
        logger.info(f"📦 RAW: {raw_data}")
        
        data = json.loads(raw_data)
        logger.info(f"✅ PARSED: {data}")
        
        # Форматируем бриф
        brief_text = f"""
📋 <b>НОВЫЙ БРИФ</b>

👤 <b>От:</b> {user.full_name} (@{user.username or 'нет'})
🆔 <b>ID:</b> <code>{user.id}</code>

━━━━━━━━━━━━━━━

<b>1️⃣ Сфера:</b> {data.get('sphere', '—')}
<b>2️⃣ Бюджет:</b> {data.get('budget', '—')}
<b>3️⃣ Сроки:</b> {data.get('timeline', '—')}
<b>4️⃣ Подробности:</b>
{data.get('details', '—')}
<b>5️⃣ Имя:</b> {data.get('name', '—')}
<b>6️⃣ Контакт:</b> {data.get('contact', '—')}
"""
        
        # Отправляем админу
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=brief_text,
            parse_mode='HTML'
        )
        logger.info(f"✅ Бриф отправлен админу")
        
        # Убираем клавиатуру и подтверждаем
        await update.message.reply_text(
            "✅ Спасибо! Ваш бриф успешно отправлен.\n"
            "Мы свяжемся с вами в ближайшее время.\n\n"
            "Чтобы заполнить ещё один бриф, напишите /start",
            reply_markup=ReplyKeyboardRemove()
        )
        logger.info("✅ Подтверждение отправлено")
        
    except Exception as e:
        logger.error(f"❌ ОШИБКА: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Произошла ошибка. Попробуйте позже.",
            reply_markup=ReplyKeyboardRemove()
        )

async def post_init(application: Application):
    """Очистка вебхуков"""
    await application.bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Вебхуки удалены")

def main():
    """Запуск"""
    if not BOT_TOKEN or not WEB_APP_URL:
        logger.error("❌ Не хватает переменных окружения!")
        return
    
    logger.info(f"🚀 Запуск бота")
    logger.info(f"🆔 ADMIN_ID = {ADMIN_ID}")
    logger.info(f"🌐 WEB_APP_URL = {WEB_APP_URL}")
    
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    
    logger.info("✅ Бот готов!")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()
