import os
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
import logging
import time
from datetime import timedelta

# Çevresel değişkenleri .env dosyasından yükle
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))  # Admin ID'lerini listeye çevir
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", ""))  # Grup chat ID'sini .env dosyasından al

# Gerekli loglama
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Veritabanı bağlantısı oluştur
conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()

# Kullanıcılar için tablo oluştur
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        expiry_epoch INTEGER
    )
''')
conn.commit()

# Admin kontrolü
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# Kalan süreyi gün, ay, yıl formatında gösteren fonksiyon
def format_remaining_time(seconds):
    delta = timedelta(seconds=seconds)
    days = delta.days
    seconds = delta.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    if days > 365:
        years = days // 365
        days = days % 365
        return f"{years} yıl, {days} gün, {hours} saat, {minutes} dakika"
    elif days > 30:
        months = days // 30
        days = days % 30
        return f"{months} ay, {days} gün, {hours} saat, {minutes} dakika"
    else:
        return f"{days} gün, {hours} saat, {minutes} dakika"

# /uyelistesi komutunun işleyicisi
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        return

    current_epoch = int(time.time())
    c.execute("SELECT user_id, expiry_epoch FROM users")
    users = c.fetchall()

    message = "Kullanıcılar ve kalan süreler:\n"
    for user in users:
        user_id, expiry_epoch = user
        remaining_time = expiry_epoch - current_epoch
        if remaining_time > 0:
            readable_time = format_remaining_time(remaining_time)
            message += f"User ID: {user_id} - Kalan süre: {readable_time}\n"
        else:
            message += f"User ID: {user_id} - Süresi dolmuş\n"

    if not users:
        message = "Kullanıcı bulunmuyor."

    await update.message.reply_text(message)

# /uyeekle komutunun işleyicisi
async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        return

    if len(context.args) != 2:
        await update.message.reply_text("Kullanım: /uyeekle <user_id> <süre>")
        return

    try:
        user_id = int(context.args[0])
        duration = context.args[1]
        duration_in_seconds = parse_duration(duration)
        if duration_in_seconds is None:
            await update.message.reply_text("Süre formatı geçersiz. Lütfen '10m', '1h', '2d' gibi bir format kullanın.")
            return

        expiry_epoch = int(time.time()) + duration_in_seconds
        c.execute("INSERT OR REPLACE INTO users (user_id, expiry_epoch) VALUES (?, ?)", (user_id, expiry_epoch))
        conn.commit()
        await update.message.reply_text(f"User ID: {user_id} eklendi, süresi: {duration}.")
    except ValueError:
        await update.message.reply_text("User ID geçersiz.")

# /suredegistir komutunun işleyicisi
async def change_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        return

    if len(context.args) != 2:
        await update.message.reply_text("Kullanım: /suredegistir <user_id> <yeni_süre>")
        return

    try:
        user_id = int(context.args[0])
        new_duration = context.args[1]
        new_duration_in_seconds = parse_duration(new_duration)
        if new_duration_in_seconds is None:
            await update.message.reply_text("Süre formatı geçersiz. Lütfen '10m', '1h', '2d' gibi bir format kullanın.")
            return

        current_epoch = int(time.time())
        c.execute("UPDATE users SET expiry_epoch = ? WHERE user_id = ?", (current_epoch + new_duration_in_seconds, user_id))
        conn.commit()
        if c.rowcount == 0:
            await update.message.reply_text("User ID bulunamadı.")
        else:
            await update.message.reply_text(f"User ID: {user_id} süresi güncellendi: {new_duration}.")
    except ValueError:
        await update.message.reply_text("User ID geçersiz.")

# Süre formatını saniyeye çeviren yardımcı fonksiyon
def parse_duration(duration_str: str) -> int:
    try:
        if duration_str.endswith('m'):
            return int(duration_str[:-1]) * 60
        elif duration_str.endswith('h'):
            return int(duration_str[:-1]) * 3600
        elif duration_str.endswith('d'):
            return int(duration_str[:-1]) * 86400
        else:
            return None
    except ValueError:
        return None

# /uyesil komutunun işleyicisi
async def delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        return

    if len(context.args) != 1:
        await update.message.reply_text("Kullanım: /uyesil <user_id>")
        return

    try:
        user_id = int(context.args[0])
        c.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()
        
        if c.rowcount == 0:
            await update.message.reply_text(f"User ID: {user_id} bulunamadı.")
        else:
            await update.message.reply_text(f"User ID: {user_id} başarıyla silindi.")
    except ValueError:
        await update.message.reply_text("User ID geçersiz.")

# Süresi dolmuş kullanıcıları gruptan kickleyen fonksiyon
async def kick_expired_users(application):
    current_epoch = int(time.time())
    c.execute("SELECT user_id FROM users WHERE expiry_epoch <= ?", (current_epoch,))
    expired_users = c.fetchall()

    if expired_users:
        for user in expired_users:
            try:
                # Kick işlemi
                await application.bot.ban_chat_member(GROUP_CHAT_ID, user[0])
                # Kicklenmiş kullanıcıyı geri getirme (ban'ı kaldırma)
                await application.bot.unban_chat_member(GROUP_CHAT_ID, user[0])
                # Kullanıcıyı veritabanından silme
                c.execute("DELETE FROM users WHERE user_id = ?", (user[0],))
                conn.commit()
                # Adminlere bilgilendirme mesajı gönder
                for admin_id in ADMIN_IDS:
                    await application.bot.send_message(admin_id, f"Süresi dolmuş kullanıcı {user[0]} gruptan kicklendi.")
            except Exception as e:
                logging.error(f"Kullanıcı {user[0]} kicklenirken hata oluştu: {e}")
                for admin_id in ADMIN_IDS:
                    await application.bot.send_message(admin_id, f"Kullanıcı {user[0]} kicklenemedi. Hata: {str(e)}")

# Botu başlat
def main():
    # Bot uygulamasını oluştur
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Komutları ve mesajları dinlemek için handler ekleme
    application.add_handler(CommandHandler("uyelistesi", list_users))
    application.add_handler(CommandHandler("uyeekle", add_user))
    application.add_handler(CommandHandler("suredegistir", change_duration))
    application.add_handler(CommandHandler("uyesil", delete_user))  # Yeni eklenen komut

    # İlk çalışmada ve düzenli olarak süresi dolmuş kullanıcıları kontrol etme
    application.job_queue.run_once(lambda context: kick_expired_users(application), when=0)  # Bot ilk başladığında hemen çalıştır
    application.job_queue.run_repeating(lambda context: kick_expired_users(application), interval=30, first=30)  # Her 30 saniyede bir düzenli kontrol

    # Botu başlat
    logging.info("Bot başlatılıyor...")
    application.run_polling()

if __name__ == "__main__":
    main()
