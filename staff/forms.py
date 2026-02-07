from django import forms
from .models import Employee

# 1. Створюємо кастомний віджет, який дозволяє вибір декількох файлів
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class EmployeeForm(forms.ModelForm):
    # Поле для вибору декількох файлів
    kep_files = forms.FileField(
        # 2. Використовуємо наш кастомний віджет
        widget=MultipleFileInput(attrs={'multiple': True, 'class': 'form-control'}),
        label="Сертифікати КЕП (Виберіть один або декілька файлів)",
        required=False
    )

    class Meta:
        model = Employee
        fields = ['full_name', 'position', 'department', 'phone', 'rnokpp']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Іванов Іван Іванович'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+380...'}),
            'rnokpp': forms.TextInput(attrs={'class': 'form-control'}),
        }