from django import forms
from .models import Employee

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

# Спеціальне поле, яке дозволяє валідувати декілька файлів одночасно
class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={'multiple': True, 'class': 'form-control'}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class EmployeeForm(forms.ModelForm):
    # Використовуємо наше нове поле MultipleFileField
    kep_files = MultipleFileField(
        label="Сертифікати КЕП (можна вибрати декілька)",
        required=False
    )

    class Meta:
        model = Employee
        fields = ['full_name', 'position', 'department', 'phone', 'rnokpp']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'rnokpp': forms.TextInput(attrs={'class': 'form-control'}),
        }