from django.contrib import admin
from .models import Asset, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'inventory_number', 'category', 'responsible_person', 'location', 'account')
    search_fields = ['name', 'inventory_number', 'barcode', 'responsible_person']
    list_filter = ('category', 'account')