import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEB_APP_URL = os.environ.get('WEB_APP_URL')
ADMIN_ID = 198218873

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет приветственное сообщение с кнопкой Mini App"""
    user = update.effective_user
    logger.info(f"🟢 Пользователь {user.id} (@{user.username}) запустил бота")
    
    button = InlineKeyboardButton(
        text="📝 Заполнить бриф",
        web_app=WebAppInfo(url=WEB_APP_URL)
    )
    keyboard = InlineKeyboardMarkup([[button]])
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я бот для сбора брифов.\n"
        "Нажми кнопку ниже, чтобы заполнить бриф.",
        reply_markup=keyboard
    )

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает данные из Mini App"""
    try:
        user = update.effective_user
        logger.info(f"🔥 ПОЛУЧЕНЫ ДАННЫЕ от пользователя {user.id}")
        
        # Получаем данные
        raw_data = update.effective_message.web_app_data.data
        logger.info(f"📦 RAW DATA: {raw_data}")
        
        data = json.loads(raw_data)
        logger.info(f"✅ PARSED DATA: {data}")
        
        # Форматируем текст брифа
        brief_text = f"""
📋 <b>НОВЫЙ БРИФ</b>

👤 <b>От:</b> {user.full_name} (@{user.username or 'нет'})
🆔 <b>ID:</b> <code>{user.id}</code>

━━━━━━━━━━━━━━━

<b>1️⃣ Сфера деятельности:</b>
{data.get('sphere', 'Не указано')}

<b>2️⃣ Бюджет проекта:</b>
{data.get('budget', 'Не указано')}

<b>3️⃣ Сроки:</b>
{data.get('timeline', 'Не указано')}

<b>4️⃣ Подробности:</b>
{data.get('details', 'Не указано')}

<b>5️⃣ Имя клиента:</b>
{data.get('name', 'Не указано')}

<b>6️⃣ Контакт:</b>
{data.get('contact', 'Не указано')}
"""
        
        # Отправляем админу
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=brief_text,
            parse_mode='HTML'
        )
        logger.info(f"✅ Бриф отправлен админу {ADMIN_ID}")
        
        # Подтверждение пользователю
        await update.message.reply_text(
            "✅ Спасибо! Ваш бриф успешно отправлен.\n"
            "Мы свяжемся с вами в ближайшее время."
        )
        logger.info("✅ Подтверждение отправлено пользователю")
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Ошибка парсинга JSON: {e}")
        logger.error(f"❌ Данные: {update.effective_message.web_app_data.data}")
        await update.message.reply_text("❌ Ошибка формата данных")
        
    except Exception as e:
        logger.error(f"❌ ОШИБКА: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Произошла ошибка при отправке. Попробуйте позже."
        )

async def post_init(application: Application):
    """Действия после инициализации"""
    await application.bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Вебхуки удалены, старые обновления пропущены")

def main():
    """Запуск бота"""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден!")
        return
    
    if not WEB_APP_URL:
        logger.error("❌ WEB_APP_URL не найден!")
        return
    
    logger.info(f"🚀 Запуск бота")
    logger.info(f"🆔 ADMIN_ID = {ADMIN_ID}")
    logger.info(f"🌐 WEB_APP_URL = {WEB_APP_URL}")
    
    # Создаем приложение
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    
    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    
    # Запуск
    logger.info("✅ Бот запущен и готов!")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()
