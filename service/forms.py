from django import forms
from .models import ServiceTask

class ServiceTaskForm(forms.ModelForm):
    class Meta:
        model = ServiceTask
        fields = ['task_type', 'device_name', 'requester_name', 'department', 'date_received', 'date_sent', 'date_returned', 'description', 'is_completed']
        widgets = {
            'date_received': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_sent': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_returned': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'is_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super(ServiceTaskForm, self).__init__(*args, **kwargs)
        # Додаємо стилі до всіх полів, крім чекбокса (він має свій клас вище)
        for field_name, field in self.fields.items():
            if field_name != 'is_completed':
                field.widget.attrs['class'] = 'form-control'