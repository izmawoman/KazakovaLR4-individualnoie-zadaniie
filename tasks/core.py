import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

# Базовые пути: корень проекта и папка для хранения данных
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)  # создаём папку data, если её нет

# Файлы для хранения попыток входа и журнала событий безопасности
ATTEMPTS_FILE = DATA_DIR / "attempts.json"
LOGS_FILE = DATA_DIR / "security_logs.json"

# Максимальное число неудачных попыток до блокировки
MAX_ATTEMPTS = 3
# Время блокировки в минутах
BLOCK_MINUTES = 5


def hash_pin(pin: str) -> str:
    """Хэширует PIN-код с помощью SHA-256 для безопасного хранения."""
    return hashlib.sha256(pin.encode("utf-8")).hexdigest()


# Словарь пользователей: имя → хэш PIN-кода
USERS = {
    "иванов": hash_pin("1234"),
    "петров": hash_pin("4321"),
    "сидоров": hash_pin("8765"),
}


def _load_json(path, default):
    """Загружает JSON-файл по указанному пути.
    Если файл не существует или повреждён — возвращает значение default."""
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default


def _save_json(path, data):
    """Сохраняет данные в JSON-файл с отступами и поддержкой кириллицы."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_username(username: str) -> str:
    """Нормализует имя пользователя: убирает пробелы и приводит к нижнему регистру."""
    return username.strip().lower()


def user_exists(username: str) -> bool:
    """Проверяет, существует ли пользователь с указанным именем."""
    return normalize_username(username) in USERS


def _load_attempts():
    """Загружает текущее состояние попыток входа из файла."""
    return _load_json(ATTEMPTS_FILE, {})


def _save_attempts(data):
    """Сохраняет состояние попыток входа в файл."""
    _save_json(ATTEMPTS_FILE, data)


class SecurityLogger:
    """Журнал событий безопасности: записывает все попытки входа."""

    def log_event(self, event_type, username, source_id, status, message):
        """Добавляет новую запись в журнал событий.
        
        Параметры:
            event_type — тип события (например, 'pin', 'identify')
            username   — имя пользователя
            source_id  — идентификатор устройства/источника
            status     — результат ('success', 'error', 'blocked')
            message    — текстовое описание события
        """
        logs = self._load_logs()
        logs.append({
            "time": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "event_type": event_type,
            "username": username,
            "source_id": source_id,
            "status": status,
            "message": message,
        })
        _save_json(LOGS_FILE, logs)

    def _load_logs(self):
        """Загружает все записи журнала из файла."""
        return _load_json(LOGS_FILE, [])


# Глобальный экземпляр журнала безопасности
LOGGER = SecurityLogger()


def get_source_state(source_id: str):
    """Возвращает текущее состояние устройства: количество неудачных попыток
    и время блокировки (или None, если не заблокировано)."""
    attempts = _load_attempts()
    return attempts.get(source_id, {
        "failed_attempts": 0,
        "blocked_until": None
    })


def get_remaining_block_seconds(source_id: str) -> int:
    """Возвращает количество секунд до снятия блокировки.
    Если устройство не заблокировано или блокировка истекла — возвращает 0."""
    state = get_source_state(source_id)
    blocked_until = state.get("blocked_until")

    if not blocked_until:
        return 0

    block_time = datetime.fromisoformat(blocked_until)
    now = datetime.now()

    if now >= block_time:
        # Блокировка истекла — сбрасываем счётчик
        attempts = _load_attempts()
        attempts[source_id] = {
            "failed_attempts": 0,
            "blocked_until": None
        }
        _save_attempts(attempts)
        return 0

    return int((block_time - now).total_seconds())


def is_source_blocked(source_id: str) -> bool:
    """Проверяет, заблокировано ли устройство прямо сейчас."""
    return get_remaining_block_seconds(source_id) > 0


def format_remaining_time(seconds: int) -> str:
    """Форматирует количество секунд в строку вида MM:SS."""
    minutes = seconds // 60
    sec = seconds % 60
    return f"{minutes:02d}:{sec:02d}"


def register_failed_attempt(username: str, source_id: str):
    """Регистрирует неудачную попытку входа с устройства.
    Если число попыток достигло MAX_ATTEMPTS — устанавливает блокировку.
    Возвращает обновлённое состояние устройства."""
    attempts = _load_attempts()
    state = attempts.get(source_id, {
        "failed_attempts": 0,
        "blocked_until": None
    })

    state["failed_attempts"] += 1

    if state["failed_attempts"] >= MAX_ATTEMPTS:
        # Достигнут лимит — блокируем устройство на BLOCK_MINUTES минут
        blocked_until = datetime.now() + timedelta(minutes=BLOCK_MINUTES)
        state["blocked_until"] = blocked_until.isoformat()

    attempts[source_id] = state
    _save_attempts(attempts)

    return state


def reset_source_attempts(source_id: str):
    """Сбрасывает счётчик неудачных попыток и снимает блокировку с устройства
    (вызывается после успешного входа)."""
    attempts = _load_attempts()
    attempts[source_id] = {
        "failed_attempts": 0,
        "blocked_until": None
    }
    _save_attempts(attempts)


def check_pin(username: str, pin: str, source_id: str) -> dict:
    """Основная функция проверки PIN-кода.
    
    Последовательно выполняет:
    1. Нормализацию и проверку существования пользователя
    2. Проверку блокировки устройства
    3. Валидацию формата PIN (4 цифры)
    4. Сравнение хэша PIN с сохранённым
    5. Регистрацию результата в журнале
    
    Возвращает словарь с ключами 'status' и 'message'.
    """
    username = normalize_username(username)

    # Проверяем, существует ли такой пользователь
    if not user_exists(username):
        LOGGER.log_event(
            event_type="identify",
            username=username,
            source_id=source_id,
            status="error",
            message="Попытка входа с несуществующим пользователем"
        )
        return {
            "status": "error",
            "message": "Пользователь не найден."
        }

    # Проверяем, не заблокировано ли устройство
    if is_source_blocked(source_id):
        remaining = get_remaining_block_seconds(source_id)
        text_time = format_remaining_time(remaining)

        LOGGER.log_event(
            event_type="pin",
            username=username,
            source_id=source_id,
            status="blocked",
            message=f"Устройство заблокировано. Осталось {text_time}"
        )
        return {
            "status": "blocked",
            "message": f"Ввод PIN-кода с устройства '{source_id}' временно заблокирован. Повторите попытку через {text_time}.",
            "remaining_seconds": remaining,
        }

    # Проверяем формат PIN: ровно 4 цифры
    if not pin.isdigit() or len(pin) != 4:
        LOGGER.log_event(
            event_type="pin",
            username=username,
            source_id=source_id,
            status="error",
            message="Некорректный формат PIN"
        )
        return {
            "status": "error",
            "message": "PIN должен состоять из 4 цифр."
        }

    # Сравниваем хэш введённого PIN с хэшем из базы
    if USERS[username] == hash_pin(pin):
        reset_source_attempts(source_id)  # сбрасываем счётчик при успехе

        LOGGER.log_event(
            event_type="pin",
            username=username,
            source_id=source_id,
            status="success",
            message="Успешный вход"
        )
        return {
            "status": "ok",
            "message": f"Вход выполнен успешно. Добро пожаловать, {username}!"
        }

    # PIN неверный — регистрируем неудачную попытку
    state = register_failed_attempt(username, source_id)
    failed_attempts = state["failed_attempts"]

    # Если после этой попытки устройство заблокировалось
    if state["blocked_until"]:
        remaining = get_remaining_block_seconds(source_id)
        text_time = format_remaining_time(remaining)

        LOGGER.log_event(
            event_type="pin",
            username=username,
            source_id=source_id,
            status="blocked",
            message=f"Устройство заблокировано после 3 неудачных попыток. Осталось {text_time}"
        )
        return {
            "status": "blocked",
            "message": f"С устройства '{source_id}' выполнено 3 неверных попытки. Ввод PIN-кода будет доступен через {text_time}.",
            "remaining_seconds": remaining,
        }

    # Устройство ещё не заблокировано — сообщаем сколько попыток осталось
    LOGGER.log_event(
        event_type="pin",
        username=username,
        source_id=source_id,
        status="error",
        message=f"Неверный PIN. Попытка {failed_attempts} из {MAX_ATTEMPTS}"
    )
    return {
        "status": "error",
        "message": f"Неверный PIN-код. Попытка {failed_attempts} из {MAX_ATTEMPTS}."
    }


def get_failed_devices():
    """Возвращает список всех событий с ошибками или блокировками
    из журнала, отсортированных от новых к старым."""
    logs = LOGGER._load_logs()
    devices = []

    for item in logs:
        if item["status"] in ["error", "blocked"]:
            devices.append({
                "time": item["time"],
                "username": item["username"],
                "source_id": item["source_id"],
                "status": item["status"],
                "message": item["message"],
            })

    return list(reversed(devices))  # переворачиваем — сначала свежие записи


from collections import Counter


def get_all_logs():
    """Возвращает все записи журнала событий безопасности."""
    return LOGGER._load_logs()


def get_log_statistics():
    """Формирует статистику по журналу для построения графиков.
    
    Считает:
    - распределение по статусам (success/error/blocked)
    - активность по устройствам
    - активность по пользователям
    - временную шкалу по часам суток
    
    Возвращает словарь с данными в формате JSON-строк для использования
    в шаблонах (Chart.js и аналогичные библиотеки).
    """
    logs = get_all_logs()

    status_counter = Counter()   # счётчик по статусам
    device_counter = Counter()   # счётчик по устройствам
    user_counter = Counter()     # счётчик по пользователям
    timeline_counter = Counter() # счётчик по часам суток

    for item in logs:
        status = item.get("status", "unknown")
        source_id = item.get("source_id", "unknown")
        username = item.get("username", "unknown")
        time_value = item.get("time", "")

        status_counter[status] += 1
        device_counter[source_id] += 1
        user_counter[username] += 1

        if time_value:
            # Извлекаем час из строки времени формата "DD.MM.YYYY HH:MM:SS"
            hour_key = time_value[11:13] if len(time_value) >= 13 else "??"
            timeline_counter[hour_key] += 1

    return {
        # Данные для графика по статусам
        "status_labels": json.dumps(list(status_counter.keys()), ensure_ascii=False),
        "status_values": json.dumps(list(status_counter.values()), ensure_ascii=False),

        # Данные для графика по устройствам
        "device_labels": json.dumps(list(device_counter.keys()), ensure_ascii=False),
        "device_values": json.dumps(list(device_counter.values()), ensure_ascii=False),

        # Данные для графика по пользователям
        "user_labels": json.dumps(list(user_counter.keys()), ensure_ascii=False),
        "user_values": json.dumps(list(user_counter.values()), ensure_ascii=False),

        # Данные для временной шкалы (по часам, отсортированно)
        "timeline_labels": json.dumps(sorted(timeline_counter.keys()), ensure_ascii=False),
        "timeline_values": json.dumps([timeline_counter[key] for key in sorted(timeline_counter.keys())], ensure_ascii=False),

        # Итоговые счётчики для карточек дашборда
        "total_logs": len(logs),
        "blocked_count": status_counter.get("blocked", 0),
        "error_count": status_counter.get("error", 0),
        "success_count": status_counter.get("success", 0),
    }
