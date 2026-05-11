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


@csrf_exempt
def identify_view(request):
    error_message = None

    if request.method == "POST":
        form = IdentifyForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"].strip().lower()
            source_id = form.cleaned_data["source_id"].strip()

            if not user_exists(username):
                error_message = "Такого пользователя нет в системе. Сначала введите корректную фамилию."
            else:
                request.session["username"] = username
                request.session["source_id"] = source_id
                return redirect("pin")
    else:
        form = IdentifyForm()

    return render(request, "tasks/identify.html", {
        "form": form,
        "error_message": error_message
    })


@csrf_exempt
def pin_view(request):
    username = request.session.get("username")
    source_id = request.session.get("source_id")

    if not username or not source_id:
        return redirect("identify")

    blocked = False
    message = None
    remaining_time = None
    remaining_seconds = 0

    if is_source_blocked(source_id):
        blocked = True
        remaining_seconds = get_remaining_block_seconds(source_id)
        remaining_time = format_remaining_time(remaining_seconds)
        message = f"Устройство '{source_id}' временно заблокировано. Повторный ввод будет доступен через {remaining_time}."

    if request.method == "POST" and not blocked:
        form = PinForm(request.POST)
        if form.is_valid():
            pin = form.cleaned_data["pin"]
            result = check_pin(username=username, pin=pin, source_id=source_id)

            message = result["message"]

            if result["status"] == "ok":
                request.session["authenticated"] = True
                return redirect("dashboard")

            if result["status"] == "blocked":
                blocked = True
                remaining_seconds = result.get("remaining_seconds", 0)
                remaining_time = format_remaining_time(remaining_seconds)
    else:
        form = PinForm()

    return render(request, "tasks/pin.html", {
        "form": form,
        "message": message,
        "blocked": blocked,
        "remaining_time": remaining_time,
        "remaining_seconds": remaining_seconds,
        "username": username,
        "source_id": source_id,
    })

def dashboard_view(request):
    if not request.session.get("authenticated"):
        return redirect("identify")

    context = get_dashboard_context()
    stats = get_log_statistics()

    context.update(stats)

    return render(request, "tasks/dashboard.html", context)

def logs_view(request):
    if not request.session.get("authenticated"):
        return redirect("identify")

    logs = LOGGER._load_logs()[::-1]
    failed_devices = get_failed_devices()

    return render(request, "tasks/logs.html", {
        "logs": logs,
        "failed_devices": failed_devices,
    })


def logout_view(request):
    request.session.flush()
    return redirect("identify")

def reset_entry_view(request):
    for key in ["username", "source_id", "authenticated"]:
        if key in request.session:
            del request.session[key]
    return redirect("identify")