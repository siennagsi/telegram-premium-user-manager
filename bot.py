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

# Botu başlat fonksiyonuna /uyesil komutunu ekleyelim
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
