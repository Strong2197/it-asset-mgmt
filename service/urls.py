from django.urls import path
from . import views


def home_view(request):
    assets_count = Asset.objects.count()

    # 1. Очікують відправки (Прийняті, але date_sent пуста)
    waiting_for_repair = ServiceTask.objects.filter(
        date_sent__isnull=True,
        is_completed=False
    ).count()

    # 2. В ремонті (Відправлені, але date_back_from_service пуста)
    in_repair_process = ServiceTask.objects.filter(
        date_sent__isnull=False,
        date_back_from_service__isnull=True,
        is_completed=False
    ).count()

    # 3. На складі (Прийшли з сервісу, але is_completed=False)
    ready_on_stock = ServiceTask.objects.filter(
        date_back_from_service__isnull=False,
        is_completed=False
    ).count()

    return render(request, 'index.html', {
        'assets_count': assets_count,
        'waiting_for_repair': waiting_for_repair,
        'in_repair_process': in_repair_process,
        'ready_on_stock': ready_on_stock
    })



urlpatterns = [
    # Головна сторінка сервісу
    path('', views.service_list, name='service_list'),

    # Створення та редагування
    path('create/', views.service_create, name='service_create'),
    path('<int:pk>/update/', views.service_update, name='service_update'),

    # --- ВИПРАВЛЕННЯ ДЛЯ НОВОГО ДИЗАЙНУ ---
    # У шаблоні ми використовуємо імена 'service_receive' та 'service_return'
    # Тут ми прив'язуємо ці імена до ваших функцій
    path('<int:pk>/receive/', views.service_receive_from_repair, name='service_receive'),
    path('<int:pk>/return/', views.service_quick_return, name='service_return'),
    # --------------------------------------

    # Друк та акти
    path('print-preview/', views.print_preview, name='print_preview'),
    path('save_report/', views.save_report, name='save_report'),

    # Історія звітів
    path('reports/', views.report_list, name='report_list'),
    path('reports/<int:pk>/', views.report_detail, name='report_detail'),
    path('reports/<int:pk>/edit/', views.report_edit, name='report_edit'),
    path('item/<int:pk>/receive/', views.item_receive, name='item_receive'),
    path('item/<int:pk>/return/', views.item_return, name='item_return'),
]