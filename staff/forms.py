from django import forms
from .models import Employee

# Створюємо спеціальний віджет, який дозволяє мультизавантаження
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class EmployeeForm(forms.ModelForm):
    # Використовуємо MultipleFileInput замість стандартного ClearableFileInput
    kep_files = forms.FileField(
        widget=MultipleFileInput(attrs={'multiple': True, 'class': 'form-control'}),
        label="Сертифікати КЕП (можна вибрати декілька)",
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