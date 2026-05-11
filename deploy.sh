#!/usr/bin/env bash
# deploy.sh — скрипт развёртывания шаблона приложения
# для веб‑контейнера аутентификации Smart Card Security

set -e

echo "=== 1. Установка Python-зависимостей из requirements.txt ==="
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
else
  echo "Файл requirements.txt не найден, пропускаю установку зависимостей."
fi

echo "=== 2. Применение миграций базы данных Django ==="
if [ -f manage.py ]; then
  python manage.py migrate --noinput
else
  echo "Файл manage.py не найден, проверь структуру проекта."
  exit 1
fi

echo "=== 3. Сбор статических файлов (если настроено STATIC_ROOT) ==="
python manage.py collectstatic --noinput || echo "collectstatic пропущен (вероятно, STATIC_ROOT не задан)."

echo "=== 4. Создание суперпользователя по умолчанию (если нет) ==="
python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()
username = "admin"
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, "admin@example.com", "admin")
    print("Создан суперпользователь admin / admin")
else:
    print("Суперпользователь admin уже существует")
EOF

echo "=== 5. Запуск сервера разработки Django ==="
# Для Replit важно слушать на 0.0.0.0 и порту из переменной $PORT (если установлена)
HOST="0.0.0.0"
PORT="${PORT:-8000}"

echo "Приложение запущено на http://${HOST}:${PORT}"
python manage.py runserver "${HOST}:${PORT}"