from django import forms
from .models import Employee


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


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
    kep_files = MultipleFileField(
        label="Сертифікати КЕП (можна вибрати декілька)",
        required=False
    )

    class Meta:
        model = Employee
        fields = [
            'full_name', 'position', 'department', 'phone', 'rnokpp',
            'appointment_date', 'appointment_order_number', 'appointment_order_file',
            'is_dismissed', 'dismissal_date', 'dismissal_order_number', 'dismissal_order_file'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            # Використовуємо TextInput, щоб Django приймав текстові значення від Select2 (tags=True)
            'position': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_position'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_department'}),

            'phone': forms.TextInput(attrs={'class': 'form-control', 'id': 'phone-mask'}),

            # Жорсткі обмеження для РНОКПП
            'rnokpp': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'rnokpp-input',
                'maxlength': '10',  # HTML ліміт
                'inputmode': 'numeric',  # Цифрова клавіатура на мобільних
                'placeholder': '1234567890'
            }),

            'appointment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'appointment_order_number': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': '№123 від 01.01.2024'}),
            'appointment_order_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.png'}),

            'is_dismissed': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'is_dismissed_check'}),

            'dismissal_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'dismissal_order_number': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': '№321 від 31.12.2024'}),
            'dismissal_order_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.png'}),
        }

    def clean_rnokpp(self):
        rnokpp = self.cleaned_data.get('rnokpp')
        if rnokpp:
            # Перевірка на стороні сервера
            if not rnokpp.isdigit():
                raise forms.ValidationError("РНОКПП повинен містити тільки цифри.")
            if len(rnokpp) != 10:
                raise forms.ValidationError(f"РНОКПП повинен містити рівно 10 цифр (зараз {len(rnokpp)}).")
        return rnokpp