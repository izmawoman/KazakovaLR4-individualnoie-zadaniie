from django import forms


class IdentifyForm(forms.Form):
    """Форма для идентификации пользователя.
    Запрашивает фамилию и идентификатор устройства перед вводом PIN-кода."""

    username = forms.CharField(
        label="Фамилия",
        max_length=20  # ограничение на длину фамилии
    )
    source_id = forms.CharField(
        label="Устройство",
        max_length=50  # идентификатор устройства (например, имя компьютера или IP)
    )


class PinForm(forms.Form):
    """Форма для ввода PIN-кода.
    Используется после успешной идентификации пользователя."""

    pin = forms.CharField(
        label="PIN-код",
        min_length=4,   # PIN должен быть не короче 4 символов
        max_length=4,   # PIN должен быть не длиннее 4 символов
        widget=forms.PasswordInput()  # скрывает вводимые символы (отображает точки)
    )
