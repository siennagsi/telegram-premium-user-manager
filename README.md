# Telegram Üye Yönetim Botu

Bu proje, bir Telegram botu ile belirli bir gruptaki üyelerin süreli olarak eklenmesini, silinmesini, sürelerinin değiştirilmesini, mevcut süreye ekleme yapılmasını ve süresi dolan üyelerin gruptan otomatik olarak çıkarılmasını sağlar. Bot, SQLite veritabanı kullanarak kullanıcı bilgilerini saklar ve yönetir.

## Proje Dosya Yapısı

Projeniz aşağıdaki dosyaları ve klasörleri içermelidir:

```
/
├── bot.py                  # Ana bot dosyası
├── .env                    # Çevresel değişkenler için yapılandırma dosyası
├── requirements.txt        # Proje bağımlılıkları
├── users.db                # SQLite veritabanı dosyası
├── /logs                   # Log dosyalarını saklamak için bir dizin (isteğe bağlı)
└── README.md               # Bu README dosyası
```

### 1. `bot.py`
Bu dosya botun ana çalıştırılabilir dosyasıdır. Botun işlevlerini yerine getiren komutlar ve fonksiyonlar burada tanımlanmıştır. Bu dosyada:
- `/uyeekle`, `/uyelistesi`, `/suredegistir`, `/sureekle`, `/uyesil` gibi komutlar ile kullanıcı yönetimi sağlanır.
- `kick_expired_users` fonksiyonu ile süresi dolmuş kullanıcılar gruptan otomatik olarak çıkarılır.

### 2. `.env`
Bu dosya, botun çalışması için gerekli çevresel değişkenleri içerir. `.env` dosyasını aşağıdaki şekilde yapılandırmalısınız:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
ADMIN_IDS=123456789,987654321  # Adminlerin Telegram ID'leri
GROUP_CHAT_ID=-1001234567890  # Yönetilecek Telegram grubunun ID'si
```

### 3. `requirements.txt`
Bu dosya, Python bağımlılıklarını listeler. Proje için gerekli paketler şunlardır:

```
python-telegram-bot==20.0
python-dotenv==0.20.0
sqlite3
```

Bağımlılıkları yüklemek için:

```bash
pip install -r requirements.txt
```

### 4. `users.db`
Bu, kullanıcı verilerinin saklandığı SQLite veritabanı dosyasıdır. Bu dosya otomatik olarak oluşturulur ve güncellenir. Veritabanı kullanıcıların ID'lerini ve üyeliklerinin bitiş zamanlarını saklar.

Tablo yapısı şu şekildedir:

```sql
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    expiry_epoch INTEGER
);
```

## Komutlar

- **/uyelistesi**: Tüm kullanıcıları ve üyeliklerinin kalan sürelerini listeler.
- **/uyeekle <user_id> <süre>**: Belirtilen kullanıcı ID'sini belirtilen süre ile gruba ekler. Süre formatı `10m`, `1h`, `2d` gibi olmalıdır.
- **/suredegistir <user_id> <yeni_süre>**: Belirtilen kullanıcı ID'sinin süresini günceller.
- **/sureekle <user_id> <eklencek_süre>**: Belirtilen kullanıcı ID'sinin mevcut süresine ek süre ekler. Süre formatı `10m`, `1h`, `2d` gibi olmalıdır.
- **/uyesil <user_id>**: Belirtilen kullanıcı ID'sini veritabanından siler ve üyeliğini iptal eder.

## Servis Olarak Çalıştırma

Botu sisteminizde servis olarak çalıştırmak için bir systemd servis dosyası oluşturabilirsiniz.

1. **Servis dosyasını oluşturun:**

    ```bash
    sudo nano /etc/systemd/system/telegram-uye-yonetim-botu.service
    ```

2. **Servis dosyasına aşağıdaki içeriği yapıştırın:**

    ```ini
    [Unit]
    Description=Telegram Üye Yönetim Botu
    After=network.target

    [Service]
    ExecStart=/usr/bin/python3 /home/ubuntu/bot.py
    WorkingDirectory=/home/ubuntu
    StandardOutput=inherit
    StandardError=inherit
    Restart=always
    User=ubuntu

    [Install]
    WantedBy=multi-user.target
    ```

3. **Servisi etkinleştirin ve başlatın:**

    ```bash
    sudo systemctl daemon-reload
    sudo systemctl start telegram-uye-yonetim-botu
    sudo systemctl enable telegram-uye-yonetim-botu
    ```

## Geliştirici Notları

- **Admin Kontrolü**: Sadece `.env` dosyasına eklenmiş adminler bot komutlarını çalıştırabilir. Admin ID'lerini güncelleyerek bu yetkilendirmeyi değiştirebilirsiniz.
- **Üye Ekleme ve Süre Formatı**: Üyelik süresini eklerken süreyi `m` (dakika), `h` (saat), veya `d` (gün) formatında belirtmelisiniz. Örneğin: `10m`, `2h`, `3d`.
- **Süresi Dolan Üyeler**: Bot her 30 saniyede bir süresi dolmuş üyeleri otomatik olarak kontrol eder ve süresi dolanları gruptan çıkarır.

## Sorun Giderme

1. **Bot Çalışmıyor**: `systemctl status telegram-uye-yonetim-botu` komutu ile botun durumu hakkında bilgi alabilirsiniz.
2. **Hatalar**: Python hatalarını görmek için sistem loglarını kontrol edin:
    ```bash
    journalctl -u telegram-uye-yonetim-botu -f
    ```

## Lisans

Bu proje MIT Lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına göz atın.
