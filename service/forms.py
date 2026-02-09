from django import forms
from .models import ServiceTask, ServiceReport
from django.db.models import Q

# Список картриджів згідно з файлом PDF
CARTRIDGE_CHOICES = [
    ('Картридж Xerox Phaser 3020, WC3025', 'Картридж Xerox Phaser 3020, WC3025'),
    ('Картридж Canon 725/ HP [CE285A]', 'Картридж Canon 725/ HP [CE285A]'),
    ('Тонер-картридж OKI MB472', 'Тонер-картридж OKI MB472'),
    ('Картридж HP [CF283A]', 'Картридж HP [CF283A]'),
    ('Картридж Canon 103/303/703/HP [Q2612A]', 'Картридж Canon 103/303/703/HP [Q2612A]'),
    ('Картридж HP [CE278A]', 'Картридж HP [CE278A]'),
    ('Картридж Canon FX-10', 'Картридж Canon FX-10'),
    ('Картридж Canon 728', 'Картридж Canon 728'),
    ('Картридж HP [Q7553A]', 'Картридж HP [Q7553A]'),
    ('Картридж Samsung MLT-D101S', 'Картридж Samsung MLT-D101S'),
    ('Картридж Canon 712/ HP [CB435A]', 'Картридж Canon 712/ HP [CB435A]'),
    ('Картридж HP [CE505A]', 'Картридж HP [CE505A]'),
    ('Картридж HP [CB436A]', 'Картридж HP [CB436A]'),
    ('Барабан OKI', 'Барабан OKI'),
]
# --- Форма 1: Для створення/редагування заявки на ремонт ---
class ServiceTaskForm(forms.ModelForm):
    class Meta:
        model = ServiceTask
        fields = ['task_type', 'device_name', 'requester_name', 'department',
                  'date_received', 'date_sent', 'date_back_from_service', 'date_returned',
                  'description', 'is_completed']
        widgets = {
            # Важливо: department тепер звичайний TextInput
            'device_name': forms.TextInput(attrs={'type': 'hidden', 'id': 'real-device-name'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'date_back_from_service': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_received': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_sent': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_returned': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'is_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super(ServiceTaskForm, self).__init__(*args, **kwargs)
        # Додаємо стилі до всіх полів, крім чекбокса
        for field_name, field in self.fields.items():
            if field_name != 'is_completed':
                field.widget.attrs['class'] = 'form-control'


# --- Форма 2: Для редагування складу звіту (Акту) ---
class ServiceReportForm(forms.ModelForm):
    class Meta:
        model = ServiceReport
        fields = ['tasks']
        widgets = {
            'tasks': forms.CheckboxSelectMultiple()
        }

    def __init__(self, *args, **kwargs):
        super(ServiceReportForm, self).__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields['tasks'].queryset = ServiceTask.objects.filter(
                Q(id__in=self.instance.tasks.values_list('id', flat=True)) |
                Q(date_sent__isnull=True)
            )
        else:
            self.fields['tasks'].queryset = ServiceTask.objects.filter(date_sent__isnull=True)

        self.fields['tasks'].label = "Оберіть картриджі для цього акту"