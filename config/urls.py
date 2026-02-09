from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.views.static import serve

from staff.models import Employee

# --- ВАЖЛИВО: Імпорти моделей ---
from inventory.models import Asset
from service.models import ServiceTask


def home_view(request):
    # Існуючий код статистики
    assets_count = Asset.objects.filter(is_archived=False).count()

    waiting_for_repair = ServiceTask.objects.filter(
        date_sent__isnull=True, is_completed=False
    ).count()

    in_repair_process = ServiceTask.objects.filter(
        date_sent__isnull=False, date_back_from_service__isnull=True, is_completed=False
    ).count()

    ready_on_stock = ServiceTask.objects.filter(
        date_back_from_service__isnull=False, is_completed=False
    ).count()

    # --- НОВЕ: Кількість працівників ---
    employees_count = Employee.objects.count()

    return render(request, 'index.html', {
        'assets_count': assets_count,
        'waiting_for_repair': waiting_for_repair,
        'in_repair_process': in_repair_process,
        'ready_on_stock': ready_on_stock,
        'employees_count': employees_count  # Передаємо в шаблон
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),

    # Підключаємо наші додатки
    path('inventory/', include('inventory.urls')),
    path('service/', include('service.urls')),
    path('docs/', include('docs.urls')),
    path('staff/', include('staff.urls')),

]

# Налаштування медіа-файлів (для картинок/документів)
#if settings.DEBUG:
 #   urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    # Примусова роздача медіа (ваші сертифікати)
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
    # Примусова роздача статики (CSS, JS, картинки дизайну)
    re_path(r'^static/(?P<path>.*)$', serve, {
        'document_root': settings.STATIC_ROOT,
    }),
]