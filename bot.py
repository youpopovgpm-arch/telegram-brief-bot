import os
import json
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEB_APP_URL = os.environ.get('WEB_APP_URL')
ADMIN_ID = 198218873

def create_pdf_brief(data, user_info):
    """Создаёт красивый PDF с брифом"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Заголовок с градиентом (имитация)
    c.setFillColorRGB(0.4, 0.49, 0.92)  # #667eea
    c.rect(0, height-60*mm, width, 60*mm, fill=1, stroke=0)
    
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height-35*mm, "БРИФ НА ДИЗАЙН САЙТА")
    
    c.setFont("Helvetica", 11)
    c.drawCentredString(width/2, height-45*mm, f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    
    y = height - 75*mm
    
    # Информация о клиенте
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20*mm, y, f"Клиент: {user_info.get('name', 'N/A')} (@{user_info.get('username', 'нет')})")
    y -= 5*mm
    c.setFont("Helvetica", 9)
    c.drawString(20*mm, y, f"ID: {user_info.get('id', 'N/A')}")
    y -= 10*mm
    
    c.setLineWidth(0.5)
    c.line(20*mm, y, width-20*mm, y)
    y -= 8*mm
    
    # Данные брифа
    sections = [
        ("О КОМПАНИИ", [
            ("Название", data.get('company')),
            ("Деятельность", data.get('business')),
            ("Что нужно", data.get('task_type')),
            ("Текущий сайт", data.get('current_site')),
        ]),
        ("ТИП И СТРУКТУРА", [
            ("Тип сайта", data.get('site_type')),
            ("Страниц", data.get('pages_count')),
            ("Разделы", data.get('key_pages')),
        ]),
        ("АУДИТОРИЯ И ЦЕЛИ", [
            ("Аудитория", data.get('target_audience')),
            ("Цели", data.get('goals')),
        ]),
        ("ДИЗАЙН", [
            ("Примеры", data.get('examples')),
            ("Стиль", data.get('style')),
            ("Цвета", data.get('colors')),
        ]),
        ("ФУНКЦИИ И РАЗРАБОТКА", [
            ("Функции", data.get('functions')),
            ("Разработка", data.get('development')),
            ("Материалы", data.get('materials')),
        ]),
        ("СРОКИ И БЮДЖЕТ", [
            ("Сроки", data.get('deadline')),
            ("Бюджет", data.get('budget')),
        ]),
        ("КОНТАКТЫ", [
            ("Имя", data.get('contact_name')),
            ("Контакт", data.get('contact')),
        ]),
    ]
    
    if data.get('extra'):
        sections.append(("ДОПОЛНИТЕЛЬНО", [("Пожелания", data.get('extra'))]))
    
    for section_title, fields in sections:
        if y < 40*mm:
            c.showPage()
            y = height - 20*mm
        
        # Заголовок секции
        c.setFillColorRGB(0.4, 0.49, 0.92)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(20*mm, y, section_title)
        y -= 6*mm
        
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 9)
        
        for label, value in fields:
            if not value or value == '—':
                continue
            
            if y < 35*mm:
                c.showPage()
                y = height - 20*mm
            
            # Лейбл жирным
            c.setFont("Helvetica-Bold", 9)
            c.drawString(22*mm, y, f"{label}:")
            y -= 4*mm
            
            # Значение с переносом
            c.setFont("Helvetica", 9)
            value_str = str(value)
            max_width = width - 50*mm
            
            if len(value_str) > 80:
                # Разбиваем на строки
                words = value_str.split()
                line = ""
                for word in words:
                    test_line = line + " " + word if line else word
                    if c.stringWidth(test_line, "Helvetica", 9) < max_width:
                        line = test_line
                    else:
                        c.drawString(25*mm, y, line)
                        y -= 4*mm
                        line = word
                        if y < 35*mm:
                            c.showPage()
                            y = height - 20*mm
                if line:
                    c.drawString(25*mm, y, line)
                    y -= 4*mm
            else:
                c.drawString(25*mm, y, value_str)
                y -= 4*mm
            
            y -= 2*mm
        
        y -= 3*mm
    
    # Футер
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawCentredString(width/2, 15*mm, "Документ создан автоматически")
    
    c.save()
    buffer.seek(0)
    return buffer

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Стартовое сообщение с кнопкой"""
    user = update.effective_user
    logger.info(f"🟢 {user.id} (@{user.username}) запустил бота")
    
    keyboard = [[KeyboardButton("📝 Заполнить бриф", web_app=WebAppInfo(url=WEB_APP_URL))]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я помогу собрать информацию о вашем проекте.\n"
        "Заполните бриф — это займёт 7-10 минут.\n\n"
        "Нажмите кнопку ниже, чтобы начать 👇",
        reply_markup=reply_markup
    )

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка данных из формы"""
    try:
        user = update.effective_user
        logger.info(f"🔥 ДАННЫЕ от {user.id}")
        
        raw_data = update.effective_message.web_app_data.data
        data = json.loads(raw_data)
        logger.info(f"✅ Parsed: {len(data)} полей")
        
        # Информация о пользователе
        user_info = {
            'id': user.id,
            'name': user.full_name,
            'username': user.username
        }
        
        # Создаём PDF
        pdf_buffer = create_pdf_brief(data, user_info)
        filename = f"brief_{user.id}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        
        # Отправляем админу
        await context.bot.send_document(
            chat_id=ADMIN_ID,
            document=pdf_buffer,
            filename=filename,
            caption=f"📋 <b>Новый бриф</b>\n\n"
                    f"👤 {user.full_name}\n"
                    f"🆔 <code>{user.id}</code>\n"
                    f"📧 @{user.username or 'нет'}\n"
                    f"💰 Бюджет: {data.get('budget', '—')}\n"
                    f"⏰ Сроки: {data.get('deadline', '—')}",
            parse_mode='HTML'
        )
        logger.info(f"✅ PDF отправлен админу")
        
        # Подтверждение клиенту
        await update.message.reply_text(
            "✅ <b>Отлично! Бриф получен.</b>\n\n"
            "Мы изучим вашу заявку и свяжемся с вами "
            "в ближайшее время для обсуждения деталей.\n\n"
            "Если хотите заполнить ещё один бриф — "
            "напишите /start",
            parse_mode='HTML',
            reply_markup=ReplyKeyboardRemove()
        )
        logger.info("✅ Подтверждение отправлено")
        
    except Exception as e:
        logger.error(f"❌ ОШИБКА: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Произошла ошибка при отправке.\n"
            "Попробуйте ещё раз или свяжитесь с нами напрямую.",
            reply_markup=ReplyKeyboardRemove()
        )

async def post_init(application: Application):
    """Очистка"""
    await application.bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Готов к работе")

def main():
    """Запуск"""
    if not BOT_TOKEN or not WEB_APP_URL:
        logger.error("❌ Нет переменных окружения!")
        return
    
    logger.info(f"🚀 Запуск")
    logger.info(f"🆔 ADMIN: {ADMIN_ID}")
    logger.info(f"🌐 URL: {WEB_APP_URL}")
    
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    
    logger.info("✅ Бот готов!")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()
