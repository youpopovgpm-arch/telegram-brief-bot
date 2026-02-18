import os
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import io

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация - ЭТО ВАЖНО!
BOT_TOKEN = "8515232202:AAHdIo0WE3qY12F4_i3L3WaQYhm7nY9w8JI"  # Ваш токен
WEB_APP_URL = "https://youpopovgpm-arch.github.io/telegram-brief-bot/"  # Ваша ссылка
ADMIN_ID = 198218873  # Ваш ID

def create_pdf(data):
    """Создает PDF файл с данными брифа"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Заголовок
    c.setFont("Helvetica-Bold", 20)
    c.drawString(30*mm, height-30*mm, "БРИФ НА ПРОЕКТ")
    
    # Дата
    c.setFont("Helvetica", 10)
    c.drawString(30*mm, height-40*mm, f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    
    # Линия
    c.line(30*mm, height-45*mm, width-30*mm, height-45*mm)
    
    # Данные
    y = height - 55*mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30*mm, y, "ДАННЫЕ КЛИЕНТА:")
    
    y -= 10*mm
    c.setFont("Helvetica", 11)
    
    fields = [
        ("Сфера деятельности", data.get('sphere', 'Не указано')),
        ("Бюджет проекта", data.get('budget', 'Не указано')),
        ("Сроки", data.get('timeline', 'Не указано')),
        ("Подробности", data.get('details', 'Не указано')),
        ("Имя", data.get('name', 'Не указано')),
        ("Контакт", data.get('contact', 'Не указано'))
    ]
    
    for label, value in fields:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(30*mm, y, f"{label}:")
        c.setFont("Helvetica", 11)
        
        # Обработка длинного текста
        if len(value) > 50:
            words = value.split()
            line = ""
            x_pos = 70*mm
            for word in words:
                if c.stringWidth(line + " " + word, "Helvetica", 11) < (width - 75*mm):
                    line += " " + word if line else word
                else:
                    c.drawString(x_pos, y, line.strip())
                    y -= 7*mm
                    line = word
            if line:
                c.drawString(x_pos, y, line.strip())
        else:
            c.drawString(70*mm, y, value)
        
        y -= 10*mm
    
    # Подпись
    y -= 10*mm
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(30*mm, y, "Документ сгенерирован автоматически ботом")
    
    c.save()
    buffer.seek(0)
    return buffer

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет приветственное сообщение с кнопкой Mini App"""
    user = update.effective_user
    logger.info(f"Пользователь {user.id} (@{user.username}) запустил бота")
    
    button = InlineKeyboardButton(
        text="📝 Заполнить бриф",
        web_app=WebAppInfo(url=WEB_APP_URL)
    )
    keyboard = InlineKeyboardMarkup([[button]])
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Нажми кнопку ниже, чтобы открыть форму и заполнить бриф.\n\n"
        "После отправки PDF файл с брифом придет сюда же!",
        reply_markup=keyboard
    )

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает данные из Mini App и отправляет PDF"""
    try:
        user = update.effective_user
        logger.info(f"🔥 ПОЛУЧЕНЫ ДАННЫЕ от пользователя {user.id}")
        
        # Получаем данные из веб-приложения
        data = json.loads(update.effective_message.web_app_data.data)
        logger.info(f"📦 Данные брифа: {data}")
        
        # Создаем PDF
        pdf_buffer = create_pdf(data)
        
        # Формируем имя файла
        filename = f"brief_{user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # ОТПРАВЛЯЕМ В ЭТОТ ЖЕ ЧАТ (где нажали кнопку)
        await context.bot.send_document(
            chat_id=update.effective_chat.id,  # ← ВАЖНО! Отправляем в этот же чат
            document=pdf_buffer,
            filename=filename,
            caption=f"📋 <b>Бриф от {user.full_name}</b>\n"
                    f"🆔 ID: <code>{user.id}</code>\n"
                    f"👤 Username: @{user.username if user.username else 'нет'}",
            parse_mode='HTML'
        )
        logger.info(f"✅ PDF отправлен в чат {update.effective_chat.id}")
        
        # Подтверждение пользователю
        await update.message.reply_text("✅ Спасибо! PDF с брифом отправлен выше ☝️")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке данных: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при отправке. Пожалуйста, попробуйте позже."
        )

async def post_init(application: Application):
    """Действия после инициализации бота"""
    await application.bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Вебхуки удалены")

def main():
    """Запуск бота"""
    logger.info(f"🚀 Запуск бота...")
    logger.info(f"🌐 WEB_APP_URL = {WEB_APP_URL}")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    
    # Запускаем бота
    logger.info("✅ Бот запущен и готов к работе!")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()
