from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.views.static import serve
from django.db.models import Sum  # <--- ВАЖЛИВО: Додаємо цей імпорт


from staff.models import Employee
from inventory.models import Asset
from service.models import ServiceTask, ServiceTaskItem

def home_view(request):
    # 1. Майно
    assets_count = Asset.objects.filter(is_archived=False).count()

    # 2. Працівники
    employees_count = Employee.objects.count()

    # --- ВИПРАВЛЕНА ЛОГІКА: Сумуємо поле 'quantity' ---

    # Очікують (Заявка ще не відправлена в сервіс)
    waiting_data = ServiceTaskItem.objects.filter(
        task__date_sent__isnull=True
    ).aggregate(total=Sum('quantity'))
    # Якщо результат None (пусто), ставимо 0
    waiting_for_repair = waiting_data['total'] or 0

    # В ремонті (Заявка відправлена, картридж ще не повернувся)
    in_repair_data = ServiceTaskItem.objects.filter(
        task__date_sent__isnull=False,
        date_back_from_service__isnull=True
    ).aggregate(total=Sum('quantity'))
    in_repair_process = in_repair_data['total'] or 0

    # Готові на складі (Повернувся, але ще не виданий)
    ready_data = ServiceTaskItem.objects.filter(
        date_back_from_service__isnull=False,
        date_returned_to_user__isnull=True
    ).aggregate(total=Sum('quantity'))
    ready_on_stock = ready_data['total'] or 0

    return render(request, 'index.html', {
        'assets_count': assets_count,
        'waiting_for_repair': waiting_for_repair,
        'in_repair_process': in_repair_process,
        'ready_on_stock': ready_on_stock,
        'employees_count': employees_count
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),

    # Підключаємо наші додатки
    path('inventory/', include('inventory.urls')),
    path('service/', include('service.urls')),
    path('docs/', include('docs.urls')),
    path('staff/', include('staff.urls')),
    path('directory/', include('directory.urls')),
]

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
    re_path(r'^static/(?P<path>.*)$', serve, {
        'document_root': settings.STATIC_ROOT,
    }),
]