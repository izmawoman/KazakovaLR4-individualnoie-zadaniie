from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from .forms import IdentifyForm, PinForm
from .core import (
    user_exists,
    check_pin,
    is_source_blocked,
    get_remaining_block_seconds,
    format_remaining_time,
    LOGGER,
    get_failed_devices,
    get_log_statistics,
)
from .risk import get_dashboard_context


@csrf_exempt  # отключаем CSRF-проверку (используется для упрощения в учебных целях)
def identify_view(request):
    """Представление для первого шага входа — идентификации пользователя.
    
    GET:  отображает пустую форму IdentifyForm.
    POST: валидирует форму, проверяет существование пользователя.
          При успехе сохраняет username и source_id в сессии
          и перенаправляет на страницу ввода PIN-кода.
    """
    error_message = None

    if request.method == "POST":
        form = IdentifyForm(request.POST)
        if form.is_valid():
            # Нормализуем: убираем пробелы и приводим к нижнему регистру
            username = form.cleaned_data["username"].strip().lower()
            source_id = form.cleaned_data["source_id"].strip()

            if not user_exists(username):
                # Пользователь не найден — показываем ошибку, не переходим дальше
                error_message = "Такого пользователя нет в системе. Сначала введите корректную фамилию."
            else:
                # Сохраняем данные в сессии для использования на следующем шаге
                request.session["username"] = username
                request.session["source_id"] = source_id
                return redirect("pin")
    else:
        # GET-запрос — просто показываем пустую форму
        form = IdentifyForm()

    return render(request, "tasks/identify.html", {
        "form": form,
        "error_message": error_message
    })


@csrf_exempt  # отключаем CSRF-проверку
def pin_view(request):
    """Представление для второго шага входа — ввода PIN-кода.
    
    Перед обработкой проверяет:
    - наличие username и source_id в сессии (иначе редирект на identify)
    - не заблокировано ли устройство
    
    GET:  отображает форму PinForm (или сообщение о блокировке).
    POST: передаёт PIN в check_pin(), обрабатывает результат.
          При успехе устанавливает флаг authenticated в сессии
          и перенаправляет на дашборд.
    """
    # Получаем данные из сессии, установленные на шаге идентификации
    username = request.session.get("username")
    source_id = request.session.get("source_id")

    # Если сессия пуста — пользователь не прошёл идентификацию, возвращаем назад
    if not username or not source_id:
        return redirect("identify")

    # Начальные значения для шаблона
    blocked = False
    message = None
    remaining_time = None
    remaining_seconds = 0

    # Проверяем, не заблокировано ли устройство прямо сейчас
    if is_source_blocked(source_id):
        blocked = True
        remaining_seconds = get_remaining_block_seconds(source_id)
        remaining_time = format_remaining_time(remaining_seconds)
        message = f"Устройство '{source_id}' временно заблокировано. Повторный ввод будет доступен через {remaining_time}."

    if request.method == "POST" and not blocked:
        # Обрабатываем форму только если устройство не заблокировано
        form = PinForm(request.POST)
        if form.is_valid():
            pin = form.cleaned_data["pin"]
            # Передаём PIN в основную логику проверки
            result = check_pin(username=username, pin=pin, source_id=source_id)

            message = result["message"]

            if result["status"] == "ok":
                # Успешный вход — устанавливаем флаг аутентификации в сессии
                request.session["authenticated"] = True
                return redirect("dashboard")

            if result["status"] == "blocked":
                # Устройство заблокировалось после этой попытки
                blocked = True
                remaining_seconds = result.get("remaining_seconds", 0)
                remaining_time = format_remaining_time(remaining_seconds)
    else:
        # GET-запрос или устройство заблокировано — показываем пустую форму
        form = PinForm()

    return render(request, "tasks/pin.html", {
        "form": form,
        "message": message,               # сообщение об ошибке или блокировке
        "blocked": blocked,               # флаг блокировки для шаблона
        "remaining_time": remaining_time, # оставшееся время блокировки (MM:SS)
        "remaining_seconds": remaining_seconds,  # то же в секундах (для JS-таймера)
        "username": username,
        "source_id": source_id,
    })


def dashboard_view(request):
    """Представление главной страницы (дашборд) с риск-анализом и статистикой.
    
    Доступно только авторизованным пользователям (проверяется флаг authenticated).
    Объединяет контекст риск-анализа и статистику журнала в один словарь.
    """
    # Защита: если пользователь не аутентифицирован — отправляем на старт
    if not request.session.get("authenticated"):
        return redirect("identify")

    # Получаем данные риск-анализа (графики, таблицы)
    context = get_dashboard_context()
    # Получаем статистику журнала (счётчики по статусам, устройствам, временная шкала)
    stats = get_log_statistics()

    # Объединяем оба словаря в один контекст для шаблона
    context.update(stats)

    return render(request, "tasks/dashboard.html", context)


def logs_view(request):
    """Представление страницы журнала событий безопасности.
    
    Доступно только авторизованным пользователям.
    Передаёт в шаблон:
    - полный журнал событий (от новых к старым)
    - список устройств с ошибками/блокировками
    """
    # Защита: незарегистрированного пользователя отправляем на идентификацию
    if not request.session.get("authenticated"):
        return redirect("identify")

    # Загружаем все логи и переворачиваем — сначала идут самые свежие
    logs = LOGGER._load_logs()[::-1]
    # Список устройств, с которых были ошибки или блокировки
    failed_devices = get_failed_devices()

    return render(request, "tasks/logs.html", {
        "logs": logs,
        "failed_devices": failed_devices,
    })


def logout_view(request):
    """Полный выход из системы.
    
    Полностью очищает сессию (удаляет все ключи, включая username,
    source_id и authenticated) и перенаправляет на страницу идентификации.
    """
    request.session.flush()  # удаляет всю сессию целиком
    return redirect("identify")


def reset_entry_view(request):
    """Сброс только данных текущего входа без полного выхода.
    
    В отличие от logout_view удаляет только ключи username, source_id
    и authenticated, не трогая другие данные сессии (например, корзину).
    Используется для кнопки «Начать заново» на странице PIN-кода.
    """
    for key in ["username", "source_id", "authenticated"]:
        if key in request.session:
            del request.session[key]
    return redirect("identify")
