from django import forms


class IdentifyForm(forms.Form):
    username = forms.CharField(
        label="Фамилия",
        max_length=20
    )
    source_id = forms.CharField(
        label="Устройство",
        max_length=50
    )


class PinForm(forms.Form):
    pin = forms.CharField(
        label="PIN-код",
        min_length=4,
        max_length=4,
        widget=forms.PasswordInput()
    )