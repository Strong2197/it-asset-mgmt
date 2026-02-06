from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from .models import ServiceTask


# --- Функція-перехідник ---
def open_print_window(modeladmin, request, queryset):
    # Збираємо ID всіх вибраних записів
    ids = ','.join(str(task.id) for task in queryset)
    url = f"/print-service/?ids={ids}"

    return HttpResponse(f"""
        <div style="text-align: center; margin-top: 100px; font-family: Arial;">
            <h2>Звіт сформовано!</h2>
            <p>У звіт потраплять лише ті записи, які <b>ще не мають дати відправки</b>.</p>

            <a href="{url}" target="_blank" style="
                background-color: #4CAF50; 
                color: white; 
                padding: 15px 32px; 
                text-align: center; 
                text-decoration: none; 
                display: inline-block; 
                font-size: 16px; 
                border-radius: 4px;">
                📄 Відкрити звіт для друку
            </a>

            <br><br><br>
            <a href="javascript:history.back()" style="color: #666;">⬅ Повернутися назад</a>
        </div>
    """)


open_print_window.short_description = "🖨️ Підготувати до друку (Тільки нові)"


# --- Реєстрація ---
@admin.register(ServiceTask)
class ServiceTaskAdmin(admin.ModelAdmin):
    # Додали 'date_sent' у список відображення
    list_display = ('device_name', 'task_type', 'department', 'date_received', 'date_sent', 'status_icon')

    # Додали фільтр по даті відправки
    list_filter = ('is_completed', 'date_received', 'date_sent')

    search_fields = ['device_name', 'requester_name']
    actions = [open_print_window]

    # Додаткова іконка для зручності
    def status_icon(self, obj):
        if obj.is_completed:
            return "✅ Готово"
        if obj.date_sent:
            return "🚚 Відправлено"
        return "📥 На складі"

    status_icon.short_description = "Статус"