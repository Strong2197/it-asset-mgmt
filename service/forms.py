from django import forms
from .models import ServiceTask, ServiceReport, ServiceTaskItem
from django.db.models import Q
from django.forms import inlineformset_factory

# --- 1. Віджети для картриджів (винесені окремо, щоб не дублювати код) ---
# Ми використовуємо цей словник в обох FormSet-ах нижче
common_widgets = {
    'item_name': forms.Select(attrs={'class': 'form-select item-select'}),
    'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'style': 'width: 80px;'}),
    'custom_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Уточнення...', 'style': 'display:none;'}),
}

# --- 2. Головна форма заявки (ваша стара форма без змін) ---
class ServiceTaskForm(forms.ModelForm):
    class Meta:
        model = ServiceTask
        fields = ['task_type', 'requester_name', 'department',
                  'date_received', 'date_sent', 'date_back_from_service', 'date_returned',
                  'description', 'is_completed']
        widgets = {
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
        for field_name, field in self.fields.items():
            if field_name != 'is_completed':
                field.widget.attrs['class'] = 'form-control'

# --- 3. Набір форм для СТВОРЕННЯ (extra=1 -> є пустий рядок) ---
ServiceItemFormSet = inlineformset_factory(
    ServiceTask, ServiceTaskItem,
    fields=['item_name', 'quantity', 'custom_name'],
    extra=1,          # <--- ТУТ 1 (додає пустий рядок при створенні)
    can_delete=True,
    widgets=common_widgets  # Використовуємо налаштування згори
)

# --- 4. Набір форм для РЕДАГУВАННЯ (extra=0 -> немає пустих рядків) ---
ServiceItemEditFormSet = inlineformset_factory(
    ServiceTask, ServiceTaskItem,
    fields=['item_name', 'quantity', 'custom_name'],
    extra=0,          # <--- ТУТ 0 (не додає зайвого рядка при редагуванні)
    can_delete=True,
    widgets=common_widgets  # Ті самі налаштування, що і вище
)

# --- 5. Форма для звіту/акту (ваша стара форма без змін) ---
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
