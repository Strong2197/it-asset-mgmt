from django import forms
from .models import Asset

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['name', 'category', 'inventory_number', 'barcode',
                  'responsible_person', 'location', 'account',
                  'purchase_date', 'notes']
        widgets = {
            # Робимо поле "Назва" меншим (rows=2) та додаємо клас auto-expand
            'name': forms.Textarea(attrs={
                'class': 'form-control auto-expand',
                'rows': 2,
                'placeholder': 'Введіть назву...'
            }),
            'purchase_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            # Для випадаючих списків (Bootstrap стиль)
            'category': forms.Select(attrs={'class': 'form-select'}),
            'responsible_person': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super(AssetForm, self).__init__(*args, **kwargs)
        # Додаємо клас form-control до всіх текстових полів, якщо вони не перевизначені у widgets
        for field_name, field in self.fields.items():
            if field_name not in ['name', 'purchase_date', 'notes', 'category', 'responsible_person', 'location', 'account']:
                field.widget.attrs['class'] = 'form-control'