import os
from pathlib import Path

# Корневая директория проекта (на два уровня выше текущего файла settings.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# Секретный ключ Django для криптографических операций (подписи сессий, токенов и т.д.)
# В продакшене обязательно задаётся через переменную окружения SECRET_KEY
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")

# Режим отладки: True только если переменная окружения DEBUG=1
# В продакшене должен быть False — иначе показываются подробные трейсбеки ошибок
DEBUG = os.getenv("DEBUG", "0") == "1"

# Список хостов, с которых Django принимает запросы
# Берётся из переменной окружения DJANGO_ALLOWED_HOSTS, по умолчанию — локальные адреса
ALLOWED_HOSTS = os.getenv(
    "DJANGO_ALLOWED_HOSTS",
    "localhost 127.0.0.1 web nginx"
).split()

# Доверенные источники для CSRF-проверки
# Нужно явно указывать домены, с которых приходят POST-запросы (особенно за reverse proxy)
CSRF_TRUSTED_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:80",
    "http://127.0.0.1:80",
    "https://*.replit.dev",   # поддержка деплоя на Replit
    "https://*.replit.app",   # поддержка деплоя на Replit
]

# Список установленных приложений Django
# Порядок важен: стандартные приложения Django + наше приложение tasks
INSTALLED_APPS = [
    "django.contrib.admin",        # административная панель
    "django.contrib.auth",         # система аутентификации
    "django.contrib.contenttypes", # фреймворк типов контента
    "django.contrib.sessions",     # поддержка сессий
    "django.contrib.messages",     # система flash-сообщений
    "django.contrib.staticfiles",  # обслуживание статических файлов
    "tasks",                       # наше основное приложение
]

# Цепочка middleware — обработчики, через которые проходит каждый запрос/ответ
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",              # заголовки безопасности (HTTPS и т.д.)
    "django.contrib.sessions.middleware.SessionMiddleware",       # поддержка сессий
    "django.middleware.common.CommonMiddleware",                  # нормализация URL (слеши и т.д.)
    "django.middleware.csrf.CsrfViewMiddleware",                  # защита от CSRF-атак
    "django.contrib.auth.middleware.AuthenticationMiddleware",    # привязка пользователя к запросу
    "django.contrib.messages.middleware.MessageMiddleware",       # поддержка flash-сообщений
    "django.middleware.clickjacking.XFrameOptionsMiddleware",     # защита от clickjacking (X-Frame-Options)
]

# Модуль с основными URL-маршрутами проекта
ROOT_URLCONF = "django_project.urls"

# Настройки шаблонизатора Django
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # папка с общими шаблонами проекта
        "APP_DIRS": True,                  # также искать шаблоны в папках templates/ каждого приложения
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",  # добавляет объект request в контекст
                "django.contrib.auth.context_processors.auth", # добавляет текущего пользователя
                "django.contrib.messages.context_processors.messages",  # добавляет flash-сообщения
            ],
        },
    },
]

# Точка входа WSGI-сервера (используется при деплое через Gunicorn, uWSGI и т.д.)
WSGI_APPLICATION = "django_project.wsgi.application"

# Настройки подключения к базе данных PostgreSQL
# Все чувствительные данные берутся из переменных окружения
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "verificationdb"),        # имя БД
        "USER": os.getenv("POSTGRES_USER", "verifuser"),           # пользователь БД
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "strongpassword"),  # пароль (не хранить в коде!)
        "HOST": os.getenv("POSTGRES_HOST", "db"),                  # хост (имя сервиса в Docker)
        "PORT": os.getenv("POSTGRES_PORT", "5432"),                # порт PostgreSQL
    }
}

# Валидаторы паролей отключены (в данном проекте используется PIN, а не пароли Django)
AUTH_PASSWORD_VALIDATORS = []

# Локализация и временная зона
LANGUAGE_CODE = "ru-ru"          # русский язык для стандартных сообщений Django
TIME_ZONE = "Europe/Moscow"      # московское время
USE_I18N = True                  # включить интернационализацию
USE_TZ = True                    # использовать timezone-aware datetime

# Настройки статических файлов (CSS, JS, изображения)
STATIC_URL = "/static/"                      # URL-префикс для статики
STATIC_ROOT = BASE_DIR / "staticfiles"       # папка, куда collectstatic собирает все файлы

# Тип автоматически создаваемого первичного ключа для моделей по умолчанию
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
