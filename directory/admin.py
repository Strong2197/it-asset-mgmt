from django.contrib import admin
from .models import PhonebookEntry


@admin.register(PhonebookEntry)
class DirectoryAdmin(admin.ModelAdmin):
    # Колонки у списку
    list_display = ('department', 'code', 'chief_name', 'email', 'chief_phone')

    # Поля, за якими працює пошук
    search_fields = ('department', 'code', 'chief_name', 'deputy_name', 'email')

    # Сортування за замовчуванням
    ordering = ('department',)

    # Групування полів у формі редагування
    fieldsets = (
        ('Загальна інформація', {
            'fields': ('department', 'code', 'email')
        }),
        ('Керівник', {
            'fields': (
                ('chief_name', 'chief_position'),
                ('chief_phone', 'chief_ip')
            )
        }),
        ('Заступник', {
            'fields': (
                'deputy_name',
                ('deputy_phone', 'deputy_ip')
            )
        }),
    )