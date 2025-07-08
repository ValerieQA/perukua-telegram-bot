# Быстрый старт Perukua Telegram Bot

## Что вам нужно получить перед запуском:

### 1. Telegram Bot Token
- Найдите @BotFather в Telegram
- Отправьте `/newbot`
- Следуйте инструкциям
- Сохраните полученный токен

### 2. OpenAI API Key
- Зайдите на https://platform.openai.com/api-keys
- Создайте новый ключ
- Сохраните ключ

### 3. Notion Integration (у вас уже есть)
- Token: `secret_...`
- Database ID: `2291985b-988d-8073-ab40-df64f8d83e44`

## Быстрая установка:

```bash
# 1. Распакуйте архив
unzip perukua_telegram_bot.zip
cd perukua_telegram_bot

# 2. Установите зависимости
pip install -r requirements.txt

# 3. Настройте переменные окружения
cp .env.example .env
# Отредактируйте .env файл, вставив ваши токены

# 4. Запустите бота
python main.py
```

## Файл .env должен содержать:

```env
TELEGRAM_BOT_TOKEN=ваш_telegram_токен
OPENAI_API_KEY=ваш_openai_ключ
NOTION_TOKEN=secret_ваш_notion_токен
NOTION_DATABASE_ID=2291985b-988d-8073-ab40-df64f8d83e44
```

## Тестирование:

1. Найдите бота в Telegram
2. Отправьте `/start`
3. Напишите: "I have an idea for a new song"
4. Проверьте, что проект появился в Notion

Готово! 🎉

