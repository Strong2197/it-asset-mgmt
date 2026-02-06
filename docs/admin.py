from django.contrib import admin
from django.utils.html import format_html
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'doc_type', 'open_link_button')
    search_fields = ['title']

    # Кнопка для відкриття посилання прямо зі списку
    def open_link_button(self, obj):
        if obj.google_drive_link:
            return format_html("<a href='{}' target='_blank' class='button'>Відкрити</a>", obj.google_drive_link)
        return "-"

    open_link_button.short_description = "Посилання"