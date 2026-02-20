from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import ServiceTask, ServiceReport, ServiceTaskItem


# --- 1. INLINE ДЛЯ КАРТРИДЖІВ ---
# Це дозволяє редагувати картриджі прямо всередині сторінки Заявки
class ServiceTaskItemInline(admin.TabularInline):
    model = ServiceTaskItem
    extra = 0  # Не показувати пусті рядки за замовчуванням
    fields = ('item_name', 'custom_name', 'quantity', 'date_back_from_service', 'date_returned_to_user')
    readonly_fields = ()  # Можна додати поля, які не можна редагувати
    min_num = 1  # Мінімум 1 картридж у заявці


# --- 2. АДМІНКА ЗАЯВОК ---
@admin.register(ServiceTask)
class ServiceTaskAdmin(admin.ModelAdmin):
    inlines = [ServiceTaskItemInline]  # Підключаємо картриджі сюди

    # Які колонки показувати в списку
    list_display = (
        'id',
        'department',
        'requester_name',
        'get_items_summary',  # Наша кастомна колонка з вмістом
        'date_received',
        'status_colored'  # Наш кольоровий статус
    )

    # Фільтри справа
    list_filter = (
        'is_completed',
        'date_received',
        'date_sent',
        'department'
    )

    # Пошук (по відділу, імені, і навіть по назві картриджа всередині)
    search_fields = [
        'department',
        'requester_name',
        'items__item_name',  # Пошук по типу картриджа
        'items__custom_name',  # Пошук по уточненню "Інше"
        'description'
    ]

    # Сортування за замовчуванням (спочатку нові)
    ordering = ('-date_received',)

    # Поля, які не можна редагувати (автоматичні дати)
    readonly_fields = ('created_at',)

    # --- Кастомні методи для колонок ---

    # 1. Гарний статус
    def status_colored(self, obj):
        if obj.is_completed:
            return format_html(
                '<span style="color: white; background-color: green; padding: 3px 10px; border-radius: 10px; font-weight: bold;">Виконано</span>'
            )
        elif obj.date_sent:
            return format_html(
                '<span style="color: white; background-color: #0d6efd; padding: 3px 10px; border-radius: 10px;">В роботі</span>'
            )
        else:
            return format_html(
                '<span style="color: black; background-color: #ffc107; padding: 3px 10px; border-radius: 10px;">Нова</span>'
            )

    status_colored.short_description = "Статус"

    # 2. Список картриджів у рядку
    def get_items_summary(self, obj):
        items = obj.items.all()
        if not items:
            return "-"

        summary = []
        for item in items:
            name = item.custom_name if item.item_name == 'Інше' else item.get_item_name_display()
            # Скорочуємо довгі назви для краси
            short_name = name.split('/')[0] if '/' in name else name
            summary.append(f"{short_name} ({item.quantity})")

        return ", ".join(summary)

    get_items_summary.short_description = "Вміст заявки"


# --- 3. АДМІНКА ЗВІТІВ (АКТІВ) ---
@admin.register(ServiceReport)
class ServiceReportAdmin(admin.ModelAdmin):
    # Додаємо 'created_at' у список відображення та поля форми
    list_display = ('id', 'created_at', 'get_total_cartridges', 'view_report_link')
    list_editable = ('created_at',)  # Дозволяє редагувати дату прямо у списку актів
    ordering = ('-created_at',)

    # Видаляємо 'created_at' з readonly_fields, щоб воно стало доступним для зміни [cite: 50]
    readonly_fields = ()

    def get_total_cartridges(self, obj):
        total = ServiceTaskItem.objects.filter(
            task__in=obj.tasks.all()
        ).aggregate(total=Sum('quantity'))['total']
        return f"{total or 0} шт."

    get_total_cartridges.short_description = "Всього картриджів"

    def view_report_link(self, obj):
        return format_html(
            f'<a href="/service/reports/{obj.pk}/" target="_blank" class="button">Відкрити Акт</a>'
        )

    view_report_link.short_description = "Дії"


# Реєструємо окремі картриджі теж, якщо треба знайти конкретний картридж без заявки
@admin.register(ServiceTaskItem)
class ServiceTaskItemAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'quantity', 'task_department', 'status_colored')
    search_fields = ('item_name', 'custom_name', 'task__department')
    list_filter = ('item_name',)

    def task_department(self, obj):
        return obj.task.department

    task_department.short_description = "Відділ"

    def status_colored(self, obj):
        if obj.date_returned_to_user:
            return format_html('<span style="color:green">Видано</span>')
        if obj.date_back_from_service:
            return format_html('<span style="color:blue">На складі</span>')
        if obj.task.date_sent:
            return format_html('<span style="color:orange">В ремонті</span>')
        return "Очікує"

    status_colored.short_description = "Статус"