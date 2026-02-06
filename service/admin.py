from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from .models import ServiceTask, ServiceReport


# --- Функція-перехідник для друку з Адмінки ---
def open_print_window(modeladmin, request, queryset):
    # Збираємо ID всіх вибраних записів через кому
    ids = ','.join(str(task.id) for task in queryset)

    # Формуємо посилання на сторінку друку
    # Шлях /service/print/ ми налаштували в service/urls.py
    url = f"/service/print/?ids={ids}"

    return HttpResponse(f"""
        <div style="text-align: center; margin-top: 100px; font-family: Arial;">
            <h2>Звіт сформовано!</h2>
            <p>Ви вибрали {queryset.count()} запис(ів).</p>
            <p>Натисніть кнопку нижче, щоб відкрити форму друку:</p>

            <a href="{url}" target="_blank" style="
                background-color: #4CAF50; 
                color: white; 
                padding: 15px 32px; 
                text-align: center; 
                text-decoration: none; 
                display: inline-block; 
                font-size: 16px; 
                border-radius: 4px;">
                📄 Відкрити звіт
            </a>

            <br><br><br>
            <a href="javascript:history.back()" style="color: #666;">⬅ Повернутися назад в адмінку</a>
        </div>
    """)


open_print_window.short_description = "🖨️ Друкувати вибрані (через сайт)"


# --- Реєстрація Журналу Ремонтів ---
@admin.register(ServiceTask)
class ServiceTaskAdmin(admin.ModelAdmin):
    list_display = ('device_name', 'task_type', 'department', 'date_received', 'date_sent', 'is_completed')
    list_filter = ('is_completed', 'date_received', 'date_sent', 'task_type')
    search_fields = ['device_name', 'requester_name', 'department']

    # Підключаємо дію друку
    actions = [open_print_window]


# --- Реєстрація Історії Роздруківок ---
@admin.register(ServiceReport)
class ServiceReportAdmin(admin.ModelAdmin):
    # Що показувати в списку
    list_display = ('__str__', 'created_at', 'get_items_count')
    # Сортування (найновіші зверху)
    ordering = ('-created_at',)
    # Поля тільки для читання (щоб випадково не змінили дату створення)
    readonly_fields = ('created_at',)

    # Додаткова колонка: рахує кількість картриджів в акті
    def get_items_count(self, obj):
        return obj.tasks.count()

    get_items_count.short_description = "К-сть позицій"