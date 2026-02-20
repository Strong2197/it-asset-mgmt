from django import forms
from .models import PhonebookEntry


class PhonebookForm(forms.ModelForm):
    class Meta:
        model = PhonebookEntry
        fields = [
            'department', 'code', 'email',
            'chief_name', 'chief_position', 'chief_phone', 'chief_ip',
            'deputy_name', 'deputy_phone', 'deputy_ip'
        ]
        widgets = {
            # Textarea дозволяє писати в кілька рядків
            'department': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Наприклад:\nІвано-Франківський відділ\nКалуський відділ'
            }),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2610, 2618'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),

            # Керівник
            'chief_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ПІБ Начальника'}),
            'chief_position': forms.TextInput(attrs={'class': 'form-control'}),
            'chief_phone': forms.TextInput(attrs={'class': 'form-control phone-mask', 'placeholder': '0xx-xxx-xx-xx'}),
            'chief_ip': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '3001'}),

            # Заступник
            'deputy_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ПІБ Заступника'}),
            'deputy_phone': forms.TextInput(attrs={'class': 'form-control phone-mask', 'placeholder': '0xx-xxx-xx-xx'}),
            'deputy_ip': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '3002'}),
        }