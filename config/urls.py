from django.contrib import admin
from django.urls import path

# Додаємо ці два імпорти:
from django.conf import settings
from django.conf.urls.static import static
from service.views import print_service_view

urlpatterns = [
    path('admin/', admin.site.urls),

    # 2. Додаємо адресу для друку
    path('print-service/', print_service_view, name='print_service'),
]

# Додаємо цю конструкцію в кінець файлу:
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "IT Відділ | Система Обліку"
admin.site.site_title = "IT Inventory"
admin.site.index_title = "Панель керування майном"