from django.contrib import admin
from .models import Employee, CareerHistory

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):

    # Які колонки показувати в списку
    list_display = (
        'id',
        'full_name',
        'position',
        'department',  # Наша кастомна колонка з вмістом
        'is_dismissed',
        'created_at'  # Наш кольоровий статус
    )
    ordering = ('-id',)
# Register your models here.
