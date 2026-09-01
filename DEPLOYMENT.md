# 🚀 Інструкція з деплою M-Truck Bot

## 📁 Структура проекту на сервері

### Розташування
```
/root/apps/m_truck_bot/
├── app/                    # Основний код додатку
├── data/                   # База даних SQLite
│   └── truck_bot.db       # Файл бази даних
├── .venv/                 # Віртуальне оточення Python (не в Git)
├── .env                   # Конфігурація (токени, налаштування)
├── .git/                  # Git репозиторій
├── requirements.txt       # Python залежності
└── README.md             # Документація
```

### Systemd Сервіс
- **Назва сервісу:** `truck-bot.service`
- **Файл конфігурації:** `/etc/systemd/system/truck-bot.service`
- **Статус:** Enabled (автозапуск при перезавантаженні сервера)
- **Користувач:** root

---

## 📤 Деплой на GitHub

### 1. Підготовка змін локально

```bash
# Перейти в папку проекту
cd D:\Project\m_truck_bot

# Перевірити статус
git status

# Додати всі зміни
git add -A

# Створити коміт
git commit -m "Опис змін"
```

### 2. Відправити на GitHub

```bash
# Пуш на GitHub
git push origin main
```

### Що включено в репозиторій:
✅ Весь код (`app/`)
✅ Залежності (`requirements.txt`)
✅ Конфігураційні файли
✅ Документація

❌ Виключено (захищено через `.gitignore`):
- `venv/` та `.venv/` - віртуальне оточення
- `data/truck_bot.db` - **база даних** (залишається локально на сервері)
- `.env` - **конфігурація з токенами** (залишається локально на сервері)
- `*.db-journal`, `*.db-wal`, `*.db-shm` - тимчасові файли БД
- `__pycache__/` - кеш Python
- Логи та тимчасові файли

**⚠️ ВАЖЛИВО:** БД та `.env` на сервері містяться актуальні дані і **НЕ перезаписуються** при `git pull`!

**GitHub репозиторій:** https://github.com/MakmillerSoft/m_truck_bot.git

---

## 🔄 Оновлення бота на сервері

### ⚠️ ВАЖЛИВО: Захист даних

**БД та .env файл НЕ включені в Git** (додано в `.gitignore`), тому:
- ✅ Локальна БД на сервері **НЕ буде перезаписана** при `git pull`
- ✅ Локальний `.env` файл **НЕ буде перезаписаний** при `git pull`
- ✅ Всі актуальні дані зберігаються на сервері

**Але для безпеки завжди робіть бекап перед оновленням!**

---

### Метод 1: Безпечне оновлення з бекапом (рекомендовано)

```bash
# 1. Підключитися до сервера
ssh root@server2102.server-vps.com

# 2. Перейти в папку проекту
cd /root/apps/m_truck_bot

# 3. 🔒 ЗРОБИТИ БЕКАП БД ТА .ENV (ОБОВ'ЯЗКОВО!)
# Створити папку для бекапів (якщо не існує)
mkdir -p /root/apps/backups

# Бекап бази даних з датою та часом
cp data/truck_bot.db /root/apps/backups/truck_bot_$(date +%Y%m%d_%H%M%S).db

# Бекап .env файлу з датою та часом
cp .env /root/apps/backups/.env_$(date +%Y%m%d_%H%M%S)

# Перевірити що бекапи створені
ls -lh /root/apps/backups/

# 4. Зупинити бота перед оновленням
systemctl stop truck-bot

# 5. Завантажити зміни з GitHub (БД та .env НЕ будуть перезаписані)
git pull origin main

# 6. Перевірити що БД та .env не змінилися
ls -lh data/truck_bot.db
ls -lh .env

# 7. Оновити залежності (якщо змінювався requirements.txt)
source .venv/bin/activate
pip install -r requirements.txt

# 8. Перезапустити бота
systemctl start truck-bot

# 9. Перевірити статус
systemctl status truck-bot

# 10. Перевірити логи
journalctl -u truck-bot -n 50 --no-pager
```

### Метод 2: Швидке оновлення (якщо впевнені що все ОК)

```bash
# 1. Підключитися до сервера
ssh root@server2102.server-vps.com

# 2. Перейти в папку проекту
cd /root/apps/m_truck_bot

# 3. Зупинити бота
systemctl stop truck-bot

# 4. Завантажити зміни з GitHub
git pull origin main

# 5. Оновити залежності (якщо потрібно)
source .venv/bin/activate
pip install -r requirements.txt

# 6. Перезапустити бота
systemctl start truck-bot

# 7. Перевірити статус
systemctl status truck-bot
```

### Метод 2: Повне переоновлення (тільки якщо git pull не працює)

**⚠️ УВАГА:** Цей метод видаляє проект і клонує заново. Обов'язково зробіть бекап!

```bash
# 1. Підключитися до сервера
ssh root@server2102.server-vps.com

# 2. Зупинити бота
systemctl stop truck-bot

# 3. Перейти в папку проекту
cd /root/apps/m_truck_bot

# 4. 🔒 ОБОВ'ЯЗКОВИЙ БЕКАП БД ТА .ENV!
mkdir -p /root/apps/backups
cp data/truck_bot.db /root/apps/backups/truck_bot_before_reclone_$(date +%Y%m%d_%H%M%S).db
cp .env /root/apps/backups/.env_before_reclone_$(date +%Y%m%d_%H%M%S)

# 5. Перейти в батьківську папку
cd /root/apps/

# 6. Перейменувати стару папку (для безпеки)
mv m_truck_bot m_truck_bot_old_$(date +%Y%m%d_%H%M%S)

# 7. Клонувати з GitHub
git clone https://github.com/MakmillerSoft/m_truck_bot.git

# 8. Перейти в нову папку
cd m_truck_bot

# 9. Відновити БД та .env з бекапу
cp /root/apps/backups/truck_bot_before_reclone_*.db data/truck_bot.db
cp /root/apps/backups/.env_before_reclone_* .env

# 10. Створити віртуальне оточення
python3 -m venv .venv

# 11. Активувати venv
source .venv/bin/activate

# 12. Встановити залежності
pip install -r requirements.txt

# 13. Перевірити що БД та .env на місці
ls -lh data/truck_bot.db
ls -lh .env

# 14. Запустити бота
systemctl start truck-bot

# 15. Перевірити статус
systemctl status truck-bot

# 16. Якщо все ОК, можна видалити стару папку (опціонально)
# cd /root/apps/
# rm -rf m_truck_bot_old_*
```

---

## 🛠️ Управління ботом через systemd

### Основні команди

```bash
# Запустити бота
systemctl start truck-bot

# Зупинити бота
systemctl stop truck-bot

# Перезапустити бота
systemctl restart truck-bot

# Перевірити статус
systemctl status truck-bot

# Дивитися логи в реальному часі
journalctl -u truck-bot -f

# Логи за останню годину
journalctl -u truck-bot --since "1 hour ago"

# Логи за сьогодні
journalctl -u truck-bot --since today

# Останні 100 рядків логів
journalctl -u truck-bot -n 100
```

### Автозапуск

```bash
# Увімкнути автозапуск при старті сервера
systemctl enable truck-bot

# Вимкнути автозапуск
systemctl disable truck-bot

# Перевірити чи увімкнено автозапуск
systemctl is-enabled truck-bot
```

---

## 🔍 Діагностика проблем

### Перевірка процесів

```bash
# Знайти процес бота
'ps aux | grep python | grep truck'

# Знайти всі Python процеси
ps aux | grep python

# Перевірити screen сесії
screen -ls
```

### Конфлікт "bot instance is running"

Якщо виникає помилка про конфлікт боту:

```bash
# 1. Знайти всі процеси Python
ps aux | grep python

# 2. Зупинити процес бота (замінити PID)
kill <PID>

# 3. Якщо не зупиняється, використати force kill
kill -9 <PID>

# 4. Перезапустити через systemd
systemctl restart truck-bot
```

### Перевірка конфігурації

```bash
# Переглянути .env файл
cat /root/apps/m_truck_bot/.env

# Перевірити права доступу
ls -la /root/apps/m_truck_bot/

# Перевірити базу даних
ls -la /root/apps/m_truck_bot/data/
```

---

## 📋 Структура systemd сервісу

Файл: `/etc/systemd/system/truck-bot.service`

```ini
[Unit]
Description=Truck Bot Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/apps/m_truck_bot
ExecStart=/root/apps/m_truck_bot/.venv/bin/python -m app.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Після зміни конфігурації:
```bash
# Перезавантажити systemd
systemctl daemon-reload

# Перезапустити сервіс
systemctl restart truck-bot
```

---

## 🔐 Важлива інформація

### Доступ до сервера
- **Хост:** server2102.server-vps.com
- **Користувач:** root
- **Шлях до бота:** `/root/apps/m_truck_bot/`

### GitHub
- **Репозиторій:** https://github.com/MakmillerSoft/m_truck_bot.git
- **Гілка:** main

### База даних
- **Тип:** SQLite
- **Файл:** `/root/apps/m_truck_bot/data/truck_bot.db`
- **Включено в Git:** ❌ НІ (захищено через `.gitignore`)
- **⚠️ ВАЖЛИВО:** БД на сервері містить актуальні дані і **НЕ перезаписується** при `git pull`
- **Бекапи:** Зберігаються в `/root/apps/backups/`

### Конфігурація
- **Файл:** `/root/apps/m_truck_bot/.env`
- **Включено в Git:** ❌ НІ (захищено через `.gitignore`)
- **⚠️ ВАЖЛИВО:** `.env` на сервері містить токени і **НЕ перезаписується** при `git pull`
- **Токен бота:** Зберігається в `.env` (BOT_TOKEN)
- **ID адміністратора:** Зберігається в `.env` (ADMIN_IDS)
- **Бекапи:** Зберігаються в `/root/apps/backups/`

---

## 🚨 Troubleshooting

### Бот не запускається

1. Перевірити логи:
   ```bash
   journalctl -u truck-bot -n 50
   ```

2. Перевірити статус:
   ```bash
   systemctl status truck-bot
   ```

3. Запустити вручну для діагностики:
   ```bash
   cd /root/apps/m_truck_bot
   source .venv/bin/activate
   python -m app.main
   ```

### Помилки з базою даних

```bash
# Перевірити файл БД
ls -la /root/apps/m_truck_bot/data/truck_bot.db

# Перевірити права доступу
chmod 644 /root/apps/m_truck_bot/data/truck_bot.db
```

### Оновлення не застосовуються

```bash
# ⚠️ УВАГА: git reset --hard видалить локальні зміни!
# Спочатку зробіть бекап БД та .env!

# Жорстке оновлення (використовуйте тільки якщо впевнені)
cd /root/apps/m_truck_bot

# Бекап перед жорстким оновленням
cp data/truck_bot.db /root/apps/backups/truck_bot_before_reset_$(date +%Y%m%d_%H%M%S).db
cp .env /root/apps/backups/.env_before_reset_$(date +%Y%m%d_%H%M%S)

# Жорстке оновлення
systemctl stop truck-bot
git fetch --all
git reset --hard origin/main

# Відновити .env (якщо він був перезаписаний)
# cp /root/apps/backups/.env_before_reset_* .env

systemctl start truck-bot
```

### Відновлення з бекапу

```bash
# Відновити БД з бекапу
cd /root/apps/m_truck_bot
systemctl stop truck-bot
cp /root/apps/backups/truck_bot_YYYYMMDD_HHMMSS.db data/truck_bot.db
systemctl start truck-bot

# Відновити .env з бекапу
cp /root/apps/backups/.env_YYYYMMDD_HHMMSS .env
systemctl restart truck-bot
```

---

## 📝 Чеклист оновлення

- [ ] Локальні зміни закомічено
- [ ] Зміни запушено на GitHub
- [ ] Підключено до сервера
- [ ] **🔒 Зроблено бекап БД** (`cp data/truck_bot.db /root/apps/backups/...`)
- [ ] **🔒 Зроблено бекап .env** (`cp .env /root/apps/backups/...`)
- [ ] Зупинено бота (`systemctl stop truck-bot`)
- [ ] Завантажено зміни (`git pull origin main`)
- [ ] Перевірено що БД та .env не змінилися
- [ ] Оновлено залежності (якщо потрібно)
- [ ] Запущено бота (`systemctl start truck-bot`)
- [ ] Перевірено статус (`systemctl status truck-bot`)
- [ ] Перевірено логи (`journalctl -u truck-bot -n 50`)
- [ ] Протестовано бота в Telegram

---

## 🔧 Поширені проблеми та рішення

### Повільна публікація авто (19+ секунд)

**Причина:** Повільна робота з базою даних або мережею.

**Рішення:**
1. Оптимізувати індекси БД
2. Додати індикатор завантаження для користувача
3. Заблокувати повторне натискання кнопки публікації

### Дублікати авто при публікації

**Причина:** Користувач натискає кнопку декілька разів через повільну відповідь.

**Рішення:**
1. Видалити дублікати через адмін панель бота
2. Додати блокування кнопки після першого натискання

### Помилка "wrong file identifier" при показі фото

**Причина:** Застарілі або невалідні file_id фотографій у базі даних.

**Рішення:**
1. Видалити авто з невалідними фото
2. Додати нові авто зі свіжими фотографіями
3. Додати обробку помилок для відсутніх фото

---

---

## 💾 Управління бекапами

### Створення бекапу вручну

```bash
# Бекап БД
cp /root/apps/m_truck_bot/data/truck_bot.db /root/apps/backups/truck_bot_$(date +%Y%m%d_%H%M%S).db

# Бекап .env
cp /root/apps/m_truck_bot/.env /root/apps/backups/.env_$(date +%Y%m%d_%H%M%S)
```

### Перегляд бекапів

```bash
# Список всіх бекапів БД
ls -lh /root/apps/backups/truck_bot_*.db

# Список всіх бекапів .env
ls -lh /root/apps/backups/.env_*

# Розмір папки з бекапами
du -sh /root/apps/backups/
```

### Очищення старих бекапів

```bash
# Видалити бекапи старіші за 30 днів
find /root/apps/backups/ -name "truck_bot_*.db" -mtime +30 -delete
find /root/apps/backups/ -name ".env_*" -mtime +30 -delete
```

---

**Останнє оновлення:** 21 листопада 2025

